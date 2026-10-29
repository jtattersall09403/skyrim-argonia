Scriptname ArgoniaCore Hidden
{ArgoniaCore's Papyrus natives (skse/ArgoniaCore). Logic stays in the plugin; scripts only call through.}

; The plugin's build version, e.g. "0.3.0".
String Function Version() global native

; Saves this playthrough has written with ArgoniaCore loaded (the META co-save family; survives save and load).
Int Function SaveCount() global native
