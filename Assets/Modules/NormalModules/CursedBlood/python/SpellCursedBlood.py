## tribalLawElection.py
## This file applies the effects of each election choice.
## Created by Alsark, 2/3/2018
from CvPythonExtensions import *
import FoxDebug
import FoxTools
from BasicFunctions import *
import CustomFunctions
import CvEventInterface

#Global
gc = CyGlobalContext()
getInfoType = gc.getInfoTypeForString
localText = CyTranslator()

def reqBloodMoon(caster):
	if caster.isHasPromotion(getInfoType('PROMOTION_WEREWOLF_FORM1')):
		return False
	if caster.isHasPromotion(getInfoType('PROMOTION_WEREWOLF_FORM2')):
		return False
	if caster.isHasPromotion(getInfoType('PROMOTION_WEREWOLF_FORM3')):
		return False
	if caster.getUnitType() == getInfoType('UNIT_DUIN'):
		return False
	if caster.getUnitType() == getInfoType('UNIT_DOVIELLO_WEREWOLF'):
		return False
	return True
