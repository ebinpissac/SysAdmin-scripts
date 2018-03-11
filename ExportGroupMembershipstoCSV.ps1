$users = Get-ADUser -Filter * 
foreach ($user in $users) {

$Groups = (Get-ADPrincipalGroupMembership -Identity $user.SamAccountName | Select-Object -ExpandProperty name) -join ','
get-aduser $user.SamAccountName -properties memberof,samaccountname,givenname,surname | select samaccountname, @{name="Groups";expression={$Groups}} | export-csv -append "ADUsers.csv" -Delimiter "," -NoTypeInformation -Encoding UTF8
}