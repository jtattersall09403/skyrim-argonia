Scriptname ANW_TravelPage extends Quest
{One page of the travel menu: a message box whose buttons open another page (Pages[i]) or move the player to the cell
named in Cells[i], as the console's coc does. Written from newworld/sources/travel/menu.json by NewWorldTravel.cs.}

Message Property Msg Auto
String[] Property Cells Auto
ANW_TravelPage[] Property Pages Auto

Function Open()
	Int b = Msg.Show()
	If b < 0 || b >= Cells.Length
		Return
	EndIf
	If Pages[b]
		Pages[b].Open()
	ElseIf Cells[b] != ""
		Debug.CenterOnCell(Cells[b])
	EndIf
EndFunction
