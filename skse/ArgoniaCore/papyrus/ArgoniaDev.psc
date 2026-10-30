Scriptname ArgoniaDev Hidden
{DEV BUILD ONLY. Registered by the windows-dev ArgoniaCore (ARGONIA_DEV_NATIVES) for the dev bridge's dev-set; never in
a release (not in the install list, not registered by the release plugin). A scene's step-0 input, through the core's clamp.}

; Sets a base skill ("longBlade" ...) clamped to 0-100; returns the value stored, -1 for an unknown skill.
Float Function SetSkill(String asSkill, Float afValue) global native
