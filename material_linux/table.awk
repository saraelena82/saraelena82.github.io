{
 print "<tr>"

 linea=""
 for(i=1;i<=NF;i++)
 {
  linea= linea " <td>"$i"</td>"; #esto es lo mas loco que he hecho...
 }
 print linea;
 
 print "</tr>"
}
