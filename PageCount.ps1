#	Written by Colin Van Alstine on 2019-06-05 upon request from Daniel Michelson
#	The goal of the script is to get an accurate page count for a folder of Word documents, in order to help prioritize project work
#	
#	Sources consulted include the following:
#	https://social.technet.microsoft.com/Forums/en-US/ad2e345a-11eb-48ed-abc2-79c36e2a9143/powershell-open-and-edit-a-protected-document?forum=worddev
#	https://devblogs.microsoft.com/scripting/use-powershell-to-find-specific-word-built-in-properties/
#	https://devblogs.microsoft.com/scripting/hey-scripting-guy-how-do-i-count-the-number-of-pages-in-a-group-of-office-word-documents/
#	https://social.technet.microsoft.com/Forums/scriptcenter/en-US/82067490-6b4e-4069-9b85-451f9a133104/how-do-i-count-the-number-of-pages-in-each-word-document-in-powershell?forum=winserverpowershell
#	https://stackoverflow.com/questions/19683973/is-there-a-way-to-force-powershell-to-open-a-document-as-read-only-and-close-wit
#	https://mcpmag.com/articles/2018/05/24/getting-started-word-using-powershell.aspx
#	
#	Improvements that could be made one day:
#	-figure out how to write-host the path and file name, so you don't need to point this at one folder at a time (currently writes the active variable, which happens to be the file name)
#	-save the results to a .csv file instead of writing to the screen
#	-get other properties or calculate other statistics


$folderPath = "C:\SSC-ACC files for import\Black Women's Health Imperative (BWHI)\*"
$fileType = "*.doc"

$word = New-Object -ComObject Word.Application
$word.Visible = $false


Function processDoc {
    $doc = $word.Documents.Open($_.FullName)

	$pages = $word.ActiveDocument.ComputeStatistics([Microsoft.Office.Interop.Word.WdStatistic]::wdStatisticPages)
	write-host "$pages	$_"
	trap [system.exception]
		{
		write-host -foreground blue "Value not found for $filename"
		continue
		}

    $doc.Close([ref]$true)
}


Get-ChildItem -Path $folderPath -Recurse -Filter $fileType | ForEach-Object { 
  processDoc
}

$word.Quit()
$word = $null
[gc]::collect() 
[gc]::WaitForPendingFinalizers()
