## tribalLawElection.py
## This file applies the effects of each election choice.
## Created by Alsark, 2/3/2018
from CvPythonExtensions import *
from BasicFunctions import *
import CvUtil
import Popup as PyPopup
import CvScreensInterface
import sys
import PyHelpers
import CustomFunctions
import ScenarioFunctions
import CvEventInterface
import Blizzards # Added in Frozen: Blizzards: TC01
import random # needed for shuffle(list)

#Global
PyInfo              = PyHelpers.PyInfo
PyPlayer            = PyHelpers.PyPlayer
gc                  = CyGlobalContext()
localText           = CyTranslator()
cf                  = CustomFunctions.CustomFunctions()
sf                  = ScenarioFunctions.ScenarioFunctions()

Manager             = CvEventInterface.getEventManager()
Bonus               = Manager.Resources
Civ                 = Manager.Civilizations
Race                = Manager.Promotions["Race"]
GenericPromo               = Manager.Promotions["Generic"]
Effect              = Manager.Promotions["Effects"]
Feature             = Manager.Feature
Terrain             = Manager.Terrain
Event               = Manager.EventTriggers
Goody               = Manager.Goodies
Mana                = Manager.Mana
UniqueImprovement   = Manager.UniqueImprovements
Improvement         = Manager.Improvements
Lair                = Manager.Lairs
Trait               = Manager.Traits
Animal              = Manager.Units["Animal"]
UnitCombat          = Manager.UnitCombats



def reqSunkenCity(caster):
    pPlot = caster.plot()
    pPlayer = gc.getPlayer(caster.getOwner())

    if pPlot.isOwned() and pPlot.getOwner() != caster.getOwner():
        return False

    if pPlot.isCityRadius():
        return False

    TERRAIN_OCEAN_DEEP = gc.getInfoTypeForString("TERRAIN_OCEAN_DEEP")
    TERRAIN_OCEAN = gc.getInfoTypeForString("TERRAIN_OCEAN")
    TERRAIN_COAST = gc.getInfoTypeForString("TERRAIN_COAST")

    #Check if the plot is Deep Ocean, Ocean, or Coast
    if pPlot.getTerrainType() not in (TERRAIN_OCEAN_DEEP, TERRAIN_OCEAN, TERRAIN_COAST):
        return False

    if pPlot.isWater():
        return True

    return True

def spellSunkenCity(caster):
    pPlot = caster.plot()
    pPlayer = gc.getPlayer(caster.getOwner())

    pCity = pPlayer.initCity(pPlot.getX(), pPlot.getY())
    pCity.setNumRealBuilding(CyGlobalContext().getInfoTypeForString('BUILDING_BEZERI_OCEAN_CITY'), 1)
    CvEventInterface.getEventManager().onCityBuilt([pCity])

def reqDrowningWaves(caster):
	pPlayer = gc.getPlayer(caster.getOwner())
	if pPlayer.isHuman() == False:
		iTeam = gc.getPlayer(caster.getOwner()).getTeam()
		pTeam = gc.getTeam(iTeam)
		if pTeam.getAtWarCount(True) < 2:
			return False
	return True

def spellDrowningWaves(caster):
	iPlayer = caster.getOwner()
	pPlayer = gc.getPlayer(iPlayer)
	map	= CyMap()
	plotByIndex	= map.plotByIndex
	for i in xrange(map.numPlots()):
            pPlot = plotByIndex(i)
            iImprovement = pPlot.getImprovementType()
            if pPlot.isOwned():
                if pPlot.getOwner() == iPlayer:
                    if pPlot.isWater() == False:
                        if pPlot.isCity() == False:
                            if iImprovement != -1 and gc.getImprovementInfo(iImprovement).isUnique(): continue
                            if pPlot.getPlotType()==PlotTypes.PLOT_HILLS:
                                pPlot.setPlotType(PlotTypes.PLOT_LAND, True, True)
                            elif pPlot.getPlotType()==PlotTypes.PLOT_PEAK:
                                pPlot.setPlotType(PlotTypes.PLOT_HILLS, True, True)
                            elif pPlot.getPlotType()==PlotTypes.PLOT_LAND:
                                pPlot.setPlotType(PlotTypes.PLOT_OCEAN, True, True)
                                pPlot.setTerrainType(gc.getInfoTypeForString("TERRAIN_COAST"),True,True)


def reqErosion(caster):
	pPlayer = gc.getPlayer(caster.getOwner())
	iTeam = pPlayer.getTeam()
	pTeam = gc.getTeam(iTeam)
	bValid = False
	getPlot	= CyMap().plot
	iRange = 1 
	for x, y in plotsInRange( caster.getX(), caster.getY(), iRange ):
		pLoopPlot = getPlot(x, y)
		if pLoopPlot.isCity() and pTeam.isAtWar(gc.getPlayer(pLoopPlot.getOwner()).getTeam()) and pLoopPlot.getPlotCity().getDefenseModifier(False)>0:
			return True
	return False

def spellErosion(caster):
	pPlayer = gc.getPlayer(caster.getOwner())
	pPlot = caster.plot()
	iTeam = pPlayer.getTeam()
	pTeam = gc.getTeam(iTeam)
	getPlot	= CyMap().plot
	iRange = 1
	for x, y in plotsInRange( caster.getX(), caster.getY(), iRange ):
		pLoopPlot = getPlot(x, y)
		if pLoopPlot.isCity() and pTeam.isAtWar(gc.getPlayer(pLoopPlot.getOwner()).getTeam()):
			pCity=pLoopPlot.getPlotCity()
			pCity.changeDefenseModifier(-5)


def reqSurging(caster):
	pPlayer = gc.getPlayer(caster.getOwner())
	pPlot = caster.plot()
	if pPlot.isWater():
		return False
	if not pPlot.isAdjacentToWater():
                return False
	if pPlot.isCity():
		return False
	if pPlot.isPeak():
                return False
	return True

def spellSurging(caster):
	pPlot = caster.plot()
	pPlot.setPlotType(PlotTypes.PLOT_OCEAN, True, True)
        pPlot.setTerrainType(gc.getInfoTypeForString("TERRAIN_COAST"),True,True)
	pPlayer = gc.getPlayer(caster.getOwner())

	if pPlot.isOwned():
		startWar(caster.getOwner(), pPlot.getOwner(), WarPlanTypes.WARPLAN_LIMITED)

def reqTsunamiKrakenweak(caster):
	gc			= CyGlobalContext()
	pPlayer 	= gc.getPlayer(caster.getOwner())
	if pPlayer.isHuman(): return True
	pTeam 		= gc.getTeam(pPlayer.getTeam())
	pCasterPlot	= caster.plot()
	getPlot	= CyMap().plot
	iRange = 2 + caster.getSpellExtraRange()
	for x,y in plotsInRange( caster.getX(), caster.getY(), iRange, 1 ):
		pPlot = getPlot(x,y)
		if not pPlot.isNone():
			if pPlot.isAdjacentToWater():
				for i in xrange(pPlot.getNumUnits()):
					pUnit = pPlot.getUnit(i)
					if pTeam.isAtWar(pUnit.getTeam()):
						return True
	return False

def spellTsunamiweak(caster):
	gc			= CyGlobalContext()
	eCold		= gc.getInfoTypeForString("DAMAGE_COLD")
	effect		= CyEngine().triggerEffect
	pCasterPlot	= caster.plot()
	randNum		= CyGame().getSorenRandNum
	getPlot	= CyMap().plot
	iRange = 1 + caster.getSpellExtraRange()
	for x,y in plotsInRange( caster.getX(), caster.getY(), iRange, 1 ):
		pPlot = getPlot(x,y)
		if not pPlot.isNone():
			if pPlot.isAdjacentToWater():
				bEffect = False
				for i in xrange(pPlot.getNumUnits()):
					pUnit = pPlot.getUnit(i)
					pUnit.doDamage(10, 40, caster, eCold, True)
					bEffect = True
				if bEffect==True:
					effect(gc.getInfoTypeForString('EFFECT_SPRING'),pPlot.getPoint())

def reqHowlingReef(caster):
    pPlot = caster.plot()
    pPlayer = gc.getPlayer(caster.getOwner())
    
    TERRAIN_OCEAN = gc.getInfoTypeForString("TERRAIN_OCEAN")

    #Check if the plot is Ocean
    if pPlot.getTerrainType() != (TERRAIN_OCEAN):
        return False

    if pPlot.isWater():
        return True

    return True

def reqPirateCity(caster):
    pPlot = caster.plot()
    pPlayer = gc.getPlayer(caster.getOwner())

    TERRAIN_COAST = gc.getInfoTypeForString("TERRAIN_COAST")

    #Check if the plot is Coast
    if pPlot.getTerrainType() != (TERRAIN_COAST):
        return False

    if pPlot.isWater():
        return True

    return True
