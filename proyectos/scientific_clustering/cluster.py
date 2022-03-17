from sys import stderr, maxint, argv
from math import factorial, exp, floor, log, fabs
from numpy import zeros, set_printoptions as spo
from random import random, choice, shuffle
from time import clock

AMPLIFY = 1.5
DAMPEN = 0.75
THRESHOLD = 0.1
DIFTHRESHOLD = 0.02
INCREASE = 1.3
# MAXITER 256: 6 
# 512: 4
# 1024: 2, 4
MAXITER = 2
ZERO = 0.000001
asymmetric = True

SARestarts = 6
SAInitialTemperature = 1.0
SACooling = 0.95
SAStopping = 6

# TIME_LIMIT 
# 256: 5
# 512: 4 
# 1024: 3
# 2048: 3
TIME_LIMIT = 3 # seconds

debug = True
HCDebug = True
ClusterDebug = True
ClusterDebugHC = False
DiffDebug = False

def degrees(cluster, elements):
    internal = 0
    total = 0
    for vertex in cluster:
        for neighbor in elements[vertex].neighbors:
            total += 1
            if neighbor in cluster:
                internal += 1
    return (internal, total)

def clusterModularity(cluster, numberOfEdges, elements):
    div = 2.0 * numberOfEdges
    (internal, total) = degrees(cluster, elements)
    return (internal/div - ((total/div)**2))

def printout(seed, members, elements, sim, asymmetric, filename, iter, time):
    if asymmetric:
        cid = seed
    else:
        cid = min(c)
    out = open(('%s_%scluster%d_iter_%d.out' % \
                    (filename, elements[cid].type(), cid, iter)), 'w')
    print >>out, '# time: ', time
    cn = len(members) 
    print >>out, '%d' % cn
    for k in members:
        v = elements[k]
        (indeg, outdeg) = members[k]
        if asymmetric and seed == k:
            print >>out, '# seed'
        print >>out, 'vertex %s %d %s %d %d' % \
            (v.tag(), len(v.projection), v.getYear(elements), indeg, outdeg)
    for k in members:
        v = elements[k]
        s = ''
        for l in members:
            if l in v.neighbors:
                # We output the edges just once.
                if k < l: 
                    w = elements[l]
                    s = getSimilarity(sim, [k, l]) + 1.0
                    # Upon outputting an article cluster, we
                    # output the words in the title, {\em
                    # without} stemming, excluding stopwords,
                    # and the year in which the article was
                    # published. The purpose of this is to
                    # include in the visualization a tag cloud
                    # for each article cluster, reflecting the
                    # relative frequencies of the title terms
                    # as well as the distribution of these
                    # mentions over time.
                    #
                    # % paragraph
                    print >>out, 'edge %s %s %f %d' % \
                        (v.tag(), w.tag(), \
                             s, \
                             v.neighbors[l])
    out.close()
    return

def pairs(list):
    n = len(list)
    for i in range(n):
        for j in range(n - i - 1):
            if list[i] is not None and list[n - j - 1] is not None:
                yield list[i], list[n - j - 1]

def c_mul(a, b):
    return eval(hex((long(a) * b) & 0xFFFFFFFFL)[:-1])

class HashableSet:
    def __init__(self, elems):
        self.h = self.computeHash(str(sorted(elems)))
        self.contents = set(elems)
    def __eq__(self, other):
        try:
            return self.contents == other.contents
        except:
            return False
    def computeHash(self, s):
        value = ord(s[0]) << 7
        for char in s:
            value = c_mul(1000003, value) ^ ord(char)
        value = value ^ len(s)
        if value == -1:
            value = -2
        return value
    def __hash__(self):
        return self.h

def getSimilarity(sim, elems):
    try:
        s = sim[HashableSet(elems)]
    except:
        s = 0.0
    return s

def setSimilarity(sim, elems, value):
    sim[HashableSet(elems)] = value
    return
                            
def fitness(cluster, vertices, sim, seed):
    global ZERO
    k = len(cluster)
    indeg = 0.0
    outdeg = 0.0
    n = len(vertices)
    # $\forall v \in C, \forall u \in \Gamma(v)$, we obtain the stored
    # similarity $s(v, w)$ and average it with the edge weight $w(v,
    # u)$.  If $u \in C$, we sum this to the {\em internal degree}
    # $d_i$; otherwise we sum it to the {\em external degree} $d_e$.
    for k in cluster:
        v = vertices[k]
        for w in v.neighbors.keys():
            s = getSimilarity(sim, [k, w])
            edgeweight = (v.weight(w) + s) / 2.0
            if w in cluster:
                indeg += edgeweight
            else:
                outdeg += edgeweight
    # All singleton clusters are defined to have fitness zero.
    #
    # % paragraph
    if k == 1:
        return (0.0, 0.0, outdeg)
    # After the iteration, we divide $d_i$ by two; this is to overcome 
    # having summed all internal contributions twice.
    indeg /=  2.0 
    # The {\em internal density} is then computed by normalizing: 
    # $\delta_i = \frac{2d_i}{|C|(|C| - 1)}$. 
    indens = (2.0 * indeg) / (k * (k - 1.0))
    div = indeg + outdeg
    if div < ZERO:
        return (0.0, indeg, outdeg)
    # The {\em relative density} is computed as $\delta_r =
    # \frac{d_i}{d_i + d_e}$.
    reldens = (1.0 * indeg) / div
    # The {\em fitness function} is then computed as $f = (\delta_i)^2
    # \delta_r$. The decision to square the internal density derives from
    # witnessing situations where a single vertex acts as a bridge between
    # two dense cliques, bringing them into a single cluster to minimize
    # the relative density, at the cost of the internal density.
    #
    # % paragraph
    fitfun = indens**2 * reldens
    return (fitfun, indeg, outdeg)


def addClusterMember(vertices, members, cand):
    indeg = 0
    outdeg = 0
    for neighbor in vertices[cand].neighbors:
        if neighbor in members:
            indeg += 1
        else:
            outdeg += 1
    members[cand] = (indeg, outdeg)
    for m in members:
        if cand in vertices[m].neighbors:
            (i, o) = members[m]
            members[m] = (i + 1, o - 1)
    return

def removeClusterMember(vertices, members, cand):
    del members[cand]
    for m in members:
        if cand in vertices[m].neighbors:
            (i, o) = members[m]
            members[m] = (i - 1, o + 1)
    return

def cluster(seed, vertices, sim, assigned, order, asymmetric, \
                filename, iter, keep=True):
    global SARestarts, SAInitialTemperature, SAStopping
    global TIME_LIMIT
#    print 'Obtaining a cluster for %d.' % seed
    before = clock()
    n = len(vertices)
    best = 0.0
    # To {\em compute a cluster} $C$, we begin with a {\em seed
    # vertex} $s$ and set initially $C = \{ s \}$.
    final = set([seed])
    # % paragraph
    #
    # A total of $R$ {\em restarts} of the procedure is made
    # (we set $R = 6$). At the end, the cluster that yielded
    # the best fitness is returned as the result.
    #
    # % paragraph
    for r in range(SARestarts):
        members = dict()
        members[seed] = (0, len(vertices[seed].neighbors))    
        temperature = SAInitialTemperature
        current = 0.0
        noProgress = 0
        # The heuristic used to choose a cluster is based on the {\em
        # simulated annealing} metaheuristic. We begin with an {\em
        # initial temperature} $T = 10$ and cool on each iteration the
        # current temperature $t$ with a {\em cooling factor} $c =
        # 0.95$; these values could be varied as parameters, but we
        # leave that to future work.
        #
        # % paragraph
        stop = SAStopping
        step = 0
        while True: 
            step += 1
            cand = None
            # We iterate over $u \in \bigcup_{v \in C} \Gamma(v)$ in
            # search of prospective new cluster members and add these
            # to a candidate set. 
            # % paragraph
            cands = set()
            cands.update(members.keys())
            for k in members:
                v = vertices[k]
                cands.update(v.neighbors.keys())
            modified = False
            options = list(cands)
            shuffle(options)
            for cand in options:
                if cand not in members:
                    if cand not in assigned:
                        addClusterMember(vertices, members, cand)
                        modified = True
                else:
                    if not keep or not (cand == seed):
                        removeClusterMember(vertices, members, cand)
                        modified = True
                if modified:
                    chosen = cand
                    break
            if not modified or len(members) == 0:
                # abandon attempts
                break
            (f, ign1, ign2) = fitness(members, vertices, sim, seed)
            accept = False
            # If it improves upon the present fitness, the
            # modified cluster is accepted. If it improves upon
            # the {\em best cluster} seen thus far for the given
            # seed vertex, the cluster and its fitness are stored.
            if f > current:
                current = f
                accept = True
                if current > best: 
                    # print 'Improvement'
                    best = current
                    final = set(members.keys())
                    noProgress = 0
                    stop -= 1
            else:
                # If there is no improvement, the modified cluster is
                # accepted with probability $p = \exp(f_c - f_m)/t$ where
                # $f_c$ is the fitness of the cluster before the 
                # modification, $f_m$ is the fitness of the modified 
                # cluster, and $t$ is the temperature (as in simulated 
                # annealing).
                #
                # % paragraph
                p = exp((f - current)/temperature)
                if p < random():
                    accept = True
                    temperature *= SACooling  
                if accept: 
                    continue;
                # If the modification was rejected, the cluster is restored
                # to its previous state. 
                if chosen in members:
                    removeClusterMember(vertices, members, chosen)
                else:
                    addClusterMember(vertices, members, chosen)
            noProgress += 1
            if noProgress >= stop:
                break 
            present = clock()
            # We have a time limit set at five seconds to interrupt
            # the local search.
            if present - before > TIME_LIMIT:
                print '.'
                break
        after = clock()
        print '# %d step steps' % step
        if len(members) >= order:
            # When outputting the cluster information, we set a
            # threshold on the cluster order to withhold the
            # printout of those clusters whose order does neither
            # match nor exceed the threshold. The purpose of such
            # filtering is to easen the computational burden of
            # the visualization phase that follows, as very small
            # clusters are often uninformative or
            # uninteresting. For each outputted clusters, a
            # drawing of the subgraph induced by the cluster is
            # produced.
            #
            # % paragraph
            printout(seed, members, vertices, sim, asymmetric, \
                         filename, iter, after - before)
            # All vertices in the produced cluster $C$ are
            # marked to have that cluster as their cluster for
            # that iteration.
            #
            # % paragraph
    return final

class Element:
    def __eq__(self, other):
        return self.id == other.id
    def __lt__(self, other):
        return self.id < other.id
    def __init__(self, ident, name):
        self.neighbors = dict()
        self.cluster = None
        self.degree = 0
        self.name = name
        self.id = ident
        self.projection = set()
    def addProjection(self, other):
        self.projection.add(other)
        return
    def replaceProjection(self, leave, enter):
        self.authors.remove(leave)
        self.authors.add(enter)
        return
    def __hash__(self):
        return self.id
    def neighbor(self, n): 
        if n == self.id:
            return 
        if n in self.neighbors:
            self.neighbors[n] += 1
        else:
            self.neighbors[n] = 1
        self.degree += 1
        return
    def weight(self, n):
        if n not in self.neighbors.keys():
            return 0.0
        else:
            # The {\em weight of an edge} $w(v, u)$ is computed as the
            # multiplicity of that edge; for purposes of the
            # clustering phase, the edges are treated as directed and
            # the weight is normalized by the degree of vertex $v$,
            # making the directed edge weight {\em asymmetric}.
            #
            # % paragraph
            w = self.neighbors[n]
            return (w * 1.0)/self.degree

class Author(Element): 
    def __init__(self, id, n):
        Element.__init__(self, id, n)
        self.name = n
        # For each author, we store the name as an (unordered) set of
        # strings, stripped of puntuation, replacing non-ASCII
        # characters with their closes ASCII match. We also associate
        # to each author a set of articles.
        #
        # % paragraph
    def type(self):
        return 'author'
    def __str__(self):
        return ' '.join(self.name)
    def tag(self):
        if self.name is None or len(self.name) == 0:
            return ''
        else:            
            return '_'.join(self.name)
    def getYear(self, elements):
        yearlist = list()
        for a in self.projection:
            e = elements[a]
            try:
                if e.year is not None:
                    yearlist.append(e.year)
            except:
                pass
        yearlist.sort()
        return ' '.join([str(y) for y in yearlist])

def recover(pairs):
    s = ''
    for (stemmed, original) in pairs:
        s += original + ' '
    return s

class Article(Element):
    def type(self):
        return 'article'
    def __init__(self, id, name):
        Element.__init__(self, id, name)
        # For each article, we store the set of authors corresponding
        # to it, the title as a set of string tokens (unordered and
        # stemmed), the journal name (also as a set of unordered and
        # stemmed string tokens), as well as the month and year of
        # publication, where available. We store for each stemmed
        # string also its original version for labeling purpose,
        # whereas the stemmed version is used in similarity
        # computations.
        #
        # % paragraph
        self.year = None
    def __str__(self):
        auth = ''
        for a in self.projection: 
            auth = auth + " & " + str(a)
        try:
            title = recover(self.name)
        except:
            title = 'N/A'
        return '%s: \"%s\", %s' \
            % (auth, title, self.year)
    def __rep__(self):
        return str(self)
    def tag(self):
        if self.name is None or len(self.name) == 0:
            return ''
        else:
            res = ''
            for (s, t) in self.name: 
                res += '_' + t
            return res
    def setYear(self, y):
        self.year = y
        return
    def getYear(self, elements):
        return str(self.year)

def simformula(i, u):
    if i == 0 or u == 0:
        return 0.0
    return (1.0/3.0)*((2.0 * i - u)/u + (i - 1.0)/i + 1.0)

def indexsim(a, b, sim):
    # For the {\em index similarity} we use instead of the
    # co-occurence of elements the similarity matrix and compute $i$
    # as the number of pairs in $A \times B$ that have nonzero similarity
    # and set $u = |A||B|$ and use Equation \ref{eq:sim} as is.
    #
    # % paragraph
    i = 0
    for first in a:
        for second in b:
            if getSimilarity(sim, [first, second]) > 0.0:
                i += 1
    return simformula(i, len(a) * len(b))

def clean(line):
    # For cleaning the input strings, we first force them into lower
    # case and replace by whitespace all occurrences of punctuation
    # and HTML tags. We then eliminate all leading and/or trailing
    # whitespace.
    #
    # % paragraph
    eliminate = '\:;,?!-/&"()$#=+*{}[]<>/'
    tags = [ '<i>', '</i>', '<sub>', '</sub>', '<sup>', '</sup>']
    line = line.strip()
    line = line.lower()
    for t in tags:
        line = line.replace(t, ' ')
    for c in eliminate:
        line = line.replace(c, ' ')
    return line.strip()

def stem(word):
    # The string-token stemming is done recursively, applying the
    # following simple rules in the order in which they are defined,
    # until none applies. \begin{enumerate}
    if len(word) >= 4 and word[-4:] in ['tion', 'ness']:
        # \item{Any token with four or more characters that ends in
        # \texttt{tion} or \texttt{ness} is stripped of that suffix.}
        return stem(word[:-4])
    if len(word) >= 3 and word[-3:] in ['tic', 'nic', 'ity', 'ing']:
        # \item{Any token with three or more characters that ends in
        # \texttt{tic}, \texttt{nic}, \texttt{ing}, or \texttt{ity} is
        # stripped of that suffix.}
        return stem(word[:-3])
    if len(word) >= 2 and word[-2:] in ['ly', 've', 'al', 'nt', 'ed']:
        # \item{Any token with three or more characters that ends in
        # \texttt{ly}, \texttt{ve}, \texttt{al}, \texttt{nt}, or
        # \texttt{ed} is stripped of that suffix.}
        return stem(word[:-2])
    if len(word) >= 2 and word[-2] == word[-1]: 
        # \item{Any token with two or more characters that ends in a
        # double occurrence of a symbol is stripped of its last
        # character.}
        return stem(word[:-1])
    if len(word) >= 1 and word[-1] in 'aeioys':
        # \item{Any token ending in a symbol in $\{a, e, i, o, y, s\}$
        # is stripped of its last character.}  
        # \end{enumerate}
        #
        # % paragraph
        return stem(word[:-1])
    return word

stopwords = ['sr', 'jr', 'von', 'van', 'de', 'del', \
'la', 'ieee', 'acm', 'siam', 'journal', 'letters', \
'reviews', 'research', 'the', 'an', 'a', 'el', 'le', \
'uno', 'una', 'un', 'for', 'of', 'from', 'with', 'to', \
'on', 'de', 'in', 'under', 'above', 'and', 'or', 'et', \
'al', 'y', 'o', 'new', 'using', 'through', 'en', 'pour', \
'por', 'les', 'auf', 'ab', 'dr', 'phd', 'results']

def stopword(word):
    # We also maintain a list of {\em stop words} to be able to filter
    # them out of article, journal, and author names. Our multilingual
    # stop-word list includes {\em articles} (such as a, an, the, una,
    # el, la), {\em prepositions} (such as from, auf, von, de),
    # titles, prefixes and suffixes typical to names of persons (such
    # as Dr., Jr.), abbreviations of associations (such as ACM, SIAM,
    # IEEE), and words that are repeted in scientific texts and
    # contribute little or none to the semantics of the name (such as
    # review, research, new, results, journal, letters). Upon
    # filtering, we also try the plural of the word if the word itself
    # is not a stop word.
    #
    # % paragraph
    return word in stopwords or word + 's' in stopwords

def process(filename, order):
    before = clock()
    log = open('%s.log' % filename, 'w')
    data = open(filename, 'r')
    elements = dict()
    sim = dict()
    lines = data.readlines()
    while len(lines) > 0:
        line = clean(lines.pop(0))
        tokens = line.split(' ')
        option = tokens.pop(0)
        if option == 'author':
            id = int(tokens.pop(0))
            line = clean(lines.pop(0)) 
            name = line.split(' ')
            a = Author(id, name)
            line = clean(lines.pop(0))
            tokens = line.split(' ')
            for t in tokens:
                t = t.strip()
                if len(t) > 0:
                    a.addProjection(int(t))
            elements[id] = a
        elif option == 'article':
            id = int(tokens.pop(0))
            line = clean(lines.pop(0)) 
            all = line.split(' ')
            name = list()
            while len(all) > 1:
                name.append((all.pop(0), all.pop(0)))
            a = Article(id, name)
            try:
                year = int(tokens.pop(0))
                a.setYear(year)
            except:
                pass
            line = clean(lines.pop(0))
            tokens = line.split(' ')
            for t in tokens:
                t = t.strip()
                if len(t) > 0:
                    a.addProjection(int(t))
            elements[id] = a
        elif option == 'sim':
            first = int(tokens.pop(0))
            second = int(tokens.pop(0))
            value = float(tokens.pop(0))
            setSimilarity(sim, [first, second], value)
    data.close()

    # Now that all duplicates have been removed, we start working with
    # the two projected graphs: the author-author graph and the
    # article-article graph.  We now iterate over the articles, taking
    # the author set of each and adding an edge in the
    # author-to-author graph whenever a coauthored article is
    # encountered. The number of coauthorships (the edge multiplicity)
    # is included as an integer property in order to use it as an edge
    # weight.  We similarly iterate over the authors, taking the set
    # of articles published by each author and adding an edge in the
    # article-to-article graph when the articles share an author.  The
    # number of shared authors (the edge multiplicity) is included as
    # an integer property in order to use it as an edge weight.
    #
    # % paragraph
    authorEdgeCount = 0
    articleEdgeCount = 0
    for e in elements:
        elem = elements[e]
        for (a, b) in pairs(list(elem.projection)):
            elements[b].neighbor(a)
            elements[a].neighbor(b)
            if (elements[a]).type() == 'author':
                authorEdgeCount += 1
            else:
                articleEdgeCount += 1

    for (a, b) in pairs(elements.keys()):        
        score = indexsim(elements[a].projection, elements[b].projection, sim)
        if score > ZERO:
            setSimilarity(sim, [a, b], score)
            #print 'Similarity of %d and %d set to %f.' % (a, b, score)
    after = clock()
    print >>log, 'Loading the data took %f seconds.' % (after - before)
    print 'Similarities have been loaded.'

    # Initially, all clusters are set as undefined.
    iter = 0
    prev = None
    while iter < MAXITER:
        iter += 1
        print 'Iteration %d' % iter
        before = clock()
        if asymmetric:
            # For an {\em asymmetric} clustering we first check
            # whether a cluster $C(b)$ for $b$ has been defined $a \in
            # C(b)$. If so, we amplify the current score, multiplying
            # it by an amplification factor (set to $1.2$ in our
            # experiments). On the contrary, if the cluster exists but
            # $a$ is not included in it, we punish the score,
            # multiplying it with a dampening constant (set to $0.9$
            # in our experiments). We then do the same for $C(a)$ to
            # check whether $b \in C(a)$. 
            #
            # % paragraph
            # This is repeated on each iteration to reward symmetrical
            # assignment and thus filter the clusters; when using the
            # symmetrical clustering mode, no iteration is needed as
            # nothing will change in the graph structure during an
            # iteration.
            #
            # % paragraph
            for (a, b) in pairs(elements.keys()):
                score = getSimilarity(sim, [a, b])
                aa = elements[a]
                ab = elements[b]
                ca = aa.cluster
                cb = ab.cluster
                if cb is not None:
                    if a in cb: 
                        score *= AMPLIFY
                    else: 
                        score *= DAMPEN;
                if ca is not None:
                    if  b in ca: 
                        score *=  AMPLIFY
                    else:
                        score *= DAMPEN 
                setSimilarity(sim, [a, b], score)

        assigned = set()
        clusters = list()
        # The ordering of the seed vertices during an iteration is a
        # random permutation.
        for a in sorted(elements.keys(), key=lambda *args: random()):
            # Upon obtaining a symmetric clustering, all vertices in a
            # computed cluster are marked as assigned and will not be
            # used again as seeds.
            #
            # % paragraph
            if asymmetric or not a in assigned:
                print 'Cluster for', a
                c = cluster(a, elements, sim, assigned, \
                                order, asymmetric, filename, iter)
                if c is not None:
                    clusters.append((a, c))
                    assigned.update(c)
                    for k in c:
                        member = elements[k]
                        previous = member.cluster
                        if previous is None or not (previous == c):
                            member.cluster = c
        penalty = 0
        authorModularity = 0.0
        articleModularity = 0.0
        for (seed, c) in clusters:
            cn = len(c) 
            if cn > 1:
                (f, id, od) = fitness(c, elements, sim, seed)
                # For each cluster, upon the postprocessing phase we
                # compute a penalty: each missing internal edge
                # provokes a unit penalty, as well as each external
                # edge connecting the cluster to the rest of the graph.
                #
                # % paragraph
                penalty += (((cn * (cn - 1)) - id) + od)
                if elements[seed].type() == 'author':
                    cm = clusterModularity(c, authorEdgeCount, elements)
                    authorModularity += cm
                else:
                    cm = clusterModularity(c, articleEdgeCount, elements)
                    articleModularity += cm
        if penalty > 0:
            penalty /= len(elements) 
        # This is then normalized by the number of vertices in total.
        after = clock()
        print >>log, \
            'Iteration %d: Computation of the clustering took %f seconds' \
            % (iter, after - before)
        print >>log, \
            'Iteration %d: Total penalty for clusters is %g' % (iter, penalty) 
        print >>log, \
            'Iteration %d: Modularity of author clustering is %f' \
            % (iter, authorModularity)
        print >>log, \
            'Iteration %d: Modularity of article clustering is %f' \
            % (iter, articleModularity)

        if not asymmetric:
            print 'Terminating a symmetrical single-iteration clustering.'
            break
        elif fabs(penalty) < THRESHOLD:
            print 'Terminating as penalty %f has magnitude below threshold %f.' \
                % (penalty, THRESHOLD)
            break
        else:
            if prev is None:
                prev = penalty
            else:
                diff = fabs(penalty - prev)
                if diff < DIFTHRESHOLD: 
                    print 'Terminating as penalty change %f is below threshold %f' \
                        % (diff, DIFTHRESHOLD)
                    break
                if penalty > prev * INCREASE:
                    print 'Terminating due to excessive penalty increase'
                    break
                prev = penalty
            # When computing symmetrical clusters, only one iteration
            # is done as nothing changes from the first iteration to
            # the second.
            #
            # % paragraph
    log.close()
    print 'Performed %d iterations of clustering' % iter

def main():
    try:
        inputfile = argv[1]
    except:
        inputfile = 'input.proc'
    try:
        order = int(argv[2])
    except:
        order = 4
    process(inputfile, order)

main()
