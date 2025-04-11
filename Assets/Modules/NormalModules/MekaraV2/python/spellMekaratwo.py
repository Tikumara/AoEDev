from CvPythonExtensions import *

gc = CyGlobalContext()
getInfoType = gc.getInfoTypeForString

Slaves = [
	getInfoType("UNIT_SLAVE"),
	getInfoType("UNIT_SLAVE_UNDEAD")
]

def reqFormSlugaBehemoth(caster):
	pPlot = caster.plot()
	iUnitType = caster.getUnitType()
	numSameTypeSlaves = 0 # Will add self
	for i in range(pPlot.getNumUnits()):
		pUnit = pPlot.getUnit(i)
		if (pUnit.isAlive() and pUnit.getOwner() == caster.getOwner() and pUnit.getUnitType() == iUnitType):
			numSameTypeSlaves += 1
	return numSameTypeSlaves >= 4

def spellFormSlugaBehemoth(caster):
	# The actual upgrading of the original unit is done in the XML,
	# so this code just kills the two lowest experienced drakes of the same type
	pPlot = caster.plot()
	iUnitType = caster.getUnitType()
	iID = caster.getID()
	sameTypeSlaves = [] # Will not include self
	for i in range(pPlot.getNumUnits()):
		pUnit = pPlot.getUnit(i)
		if (pUnit.isAlive() and pUnit.getOwner() == caster.getOwner() and pUnit.getUnitType() == iUnitType and pUnit.getID() != iID):
			sameTypeSlaves.append(pUnit)
	sameTypeSlaves.sort(cmp = lambda a, b: a.getExperienceTimes100() - b.getExperienceTimes100())
	for i in range(2):
		if sameTypeSlaves[i].isImmortal():
			sameTypeSlaves[i].changeImmortal(-10)
		sameTypeSlaves[i].kill(True, 0)

