#Ebin Issac 6/3/2018
#This will read a list of servers from a text file, and extract the services which are not run by localsystem, and save into a csv file. Need to be run from a server with elevated permissions

$ComputerList = Get-Content serverlist.txt
ForEach ($Server In $ComputerList) {
    Write-Host "Processing $($Server) ... " -ForegroundColor White -NoNewline
    Get-wmiobject -computername $Server win32_service | where { $_.startname -notmatch "localsystem"}| select-object pscomputername,Displayname,name,startname | Export-Csv "$Server.csv" -NoTypeInformation 
   # write-host $?
    If ($? -eq 'True') {
			Write-Host "OK." -ForegroundColor Green
    }
     Else {
			Write-Host "Failed." -ForegroundColor Red
    }
}