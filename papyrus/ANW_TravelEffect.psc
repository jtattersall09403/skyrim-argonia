Scriptname ANW_TravelEffect extends ActiveMagicEffect
{The effect of the lesser power "Argonia Travel": opens the root page of the travel menu (newworld/sources/travel/menu.json).}

ANW_TravelPage Property Root Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Root.Open()
EndEvent
