## Sid Meier's Civilization 4
## Copyright Firaxis Games 2005
##
## Implementaion of miscellaneous game functions

import CvUtil
from CvPythonExtensions import *
from BasicFunctions import *
import CvEventInterface
import CustomFunctions
import ScenarioFunctions

## *******************
## Modular Python: ANW 16-feb-2010
##                     29-may-2010
##                     20-aug-2010
## ArcticNightWolf on CivFanatics
## ArcticNightWolf@gmail.com

# For dynamic plugin loading
import imp    # dynamic importing of libraries
#import glob   # Unix style pathname pattern expansion
import os
import CvPath # path to current assets
import inspect

# Maps modules to the function name
# Syntax: {'functionName': [module1, module2]}
command = {}

# functionList is a list of strings of functions we will directly map
functionList = ['isVictoryTest', 'isVictory', 'isPlayerResearch', 'getExtraCost', 'createBarbarianCities', 'createBarbarianUnits', 'createBarbarianBosses',
 'skipResearchPopup', 'showTechChooserButton', 'getFirstRecommendedTech', 'getSecondRecommendedTech', 'canRazeCity', 'canDeclareWar', 'skipProductionPopup',
 'showExamineCityButton', 'getRecommendedUnit', 'getRecommendedBuilding', 'updateColoredPlots', 'isActionRecommended', 'unitCannotMoveInto', 'cannotHandleAction',
 'canBuild', 'cannotFoundCity', 'cannotSelectionListMove', 'cannotSelectionListGameNetMessage', 'cannotDoControl', 'canResearch', 'cannotResearch', 'canDoCivic',
 'cannotDoCivic', 'canTrain', 'cannotTrain', 'canConstruct', 'cannotConstruct', 'canCreate', 'cannotCreate', 'canMaintain', 'cannotMaintain', 'AI_chooseTech',
 'AI_chooseProduction', 'AI_unitUpdate', 'AI_doWar', 'AI_doDiplo', 'calculateScore', 'doHolyCity', 'doHolyCityTech', 'doGold', 'doResearch', 'doGoody', 'doGrowth',
 'cannotGrow', 'cannotStarve', 'cannotSpreadReligionHere', 'doProduction', 'doCulture', 'doPlotCulture', 'doReligion', 'cannotSpreadReligion', 'doGreatPeople',
 'doMeltdown', 'doReviveActivePlayer', 'doPillageGold', 'doCityCaptureGold', 'citiesDestroyFeatures', 'canFoundCitiesOnWater', 'doCombat', 'getConscriptUnitType',
 'getCityFoundValue', 'canPickPlot', 'getUnitCostMod', 'getBuildingCostMod', 'canUpgradeAnywhere', 'getWidgetHelp', 'getUpgradePriceOverride', 'getExperienceNeeded']

## Modular Python End
## *******************

class CvGameUtils:
	"Miscellaneous game functions"
	def __init__(self):

		## *******************
		## Modular Python: ANW 29-may-2010

		self.pluginScan()

		## Modular Python End
		## *******************

		pass

################# MODULAR PYTHON HANDLER ############
## Modular Python: ANW 16-feb-2010
##                     29-may-2010
##                     20-aug-2010
##                     02-sep-2010

	def pluginScan(self):
		#print ("PluginScan called")
		for function in functionList:
			command[function] = []
		# Load modules
		MLFlist = []
		MLFlist.append(CvPath.assetsPath[2] + "\\Modules\\NormalModules\\")
		MLFlist.append(CvPath.assetsPath[2] + "\\Modules\\LoadOrderVitalModules\\FirstLoad\\")
		MLFlist.append(CvPath.assetsPath[2] + "\\Modules\\LoadOrderVitalModules\\SecondLoad\\")
		MLFlist.append(CvPath.assetsPath[2] + "\\Modules\\LoadOrderVitalModules\\ThirdLoad\\")
		MLFlist.append(CvPath.assetsPath[2] + "\\Modules\\LoadOrderVitalModules\\FourthLoad\\")

		for pathToMLF in MLFlist:
			for modules in os.listdir(pathToMLF):
				pathToModuleRoot = pathToMLF+modules+"\\"
				# Ignore all xml files
				if modules.lower()[-4:] != ".xml":
					# Check whether path exists // whether current directory isn't actually a file
					if os.path.exists(pathToModuleRoot):
						# Check whether python folder is present
						if "python" in os.listdir(pathToModuleRoot):
							pathToModulePython = pathToModuleRoot+"python\\"
							# For every file in that folder
							for pythonFileSourceName in os.listdir(pathToModulePython):
								pythonFileSource = pathToModulePython+pythonFileSourceName
								# Is it non-python file ?
								if (pythonFileSource.lower()[-3:] != ".py"):
									continue
								# Is it spell file ?
								if pythonFileSource.replace ( '.py', '' ).replace ( '\\', '/' ).split ( '/' ) [ -1 ].upper()[0:5] == "SPELL":
									continue
								# Is it event file ?
								if pythonFileSource.replace ( '.py', '' ).replace ( '\\', '/' ).split ( '/' ) [ -1 ].upper()[0:5] == "EVENT":
									continue
								tempFileName = file(pythonFileSource)
								tempModuleName = pythonFileSource.replace ( '.py', '' ).replace ( '\\', '/' ).split ( '/' ) [ -1 ]
								module = imp.load_module( tempModuleName, tempFileName, tempModuleName+".py", ("","",1))
								# List all the functions the plugin has.
								functs = inspect.getmembers(module, inspect.isfunction)
								#each function is returned as a tuple (or maybe a list) 0, being the name, and 1 being the function itself
								for tuple in functs:
									for possFuncts in functionList:
										#since we only need the name of the function to match up, we only use the name in [0]
										if tuple[0] == possFuncts:
											#add it to our list of the applicable functions.
											command[possFuncts].append(module)
								tempFileName.close()

## Modular Python end
#################### ON EVENTS ######################

	def isVictoryTest(self):		#Return False to prevent testing for Victory
		## modified: estyles 25-Oct-2010 to allow this function to be modular

		if ( CyGame().getElapsedGameTurns() <= 10 ):
			return False

		## *******************
		## Modular Python: estyles 25-Oct-2010

		for module in command['isVictoryTest']:
			if not module.isVictoryTest(self):
				return False

		## Modular Python End
		## *******************

		return True

	def isVictory(self, argsList):		#Return True to grant the Tested Team a Victory.  If more than 1 team gains Victory in a single turn, a single winner is selected randomly
		eVictory = argsList[0]
		Manager	= CvEventInterface.getEventManager()
		if eVictory == Manager.Victories["Gone to Hell"]: return False

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['isVictory']:
			if not module.isVictory(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def isPlayerResearch(self, argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['isPlayerResearch']:
			if not module.isPlayerResearch(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def getExtraCost(self, argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		modularReturn = 0
		for module in command['getExtraCost']:
			modularReturn += module.getExtraCost(self, argsList)
		return modularReturn

		## Modular Python End
		## *******************

		#return 0

	def createBarbarianCities(self):

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['createBarbarianCities']:
			if module.createBarbarianCities(self):
				return True

		## Modular Python End
		## *******************

		return False

	def createBarbarianUnits(self):

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['createBarbarianUnits']:
			if module.createBarbarianUnits(self):
				return True

		## Modular Python End
		## *******************

		return False

	def createBarbarianBosses(self, argsList):
		pPlot = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['createBarbarianBosses']:
			if module.createBarbarianBosses(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def skipResearchPopup(self,argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['skipResearchPopup']:
			if module.skipResearchPopup(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def showTechChooserButton(self,argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['showTechChooserButton']:
			if not module.showTechChooserButton(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def getFirstRecommendedTech(self,argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getFirstRecommendedTech']:
			modularReturn = module.getFirstRecommendedTech(self, argsList)
			if modularReturn != TechTypes.NO_TECH:
				return modularReturn

		## Modular Python End
		## *******************

		return TechTypes.NO_TECH

	def getSecondRecommendedTech(self,argsList):
		ePlayer = argsList[0]
		eFirstTech = argsList[1]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getSecondRecommendedTech']:
			modularReturn = module.getSecondRecommendedTech(self, argsList)
			if modularReturn != TechTypes.NO_TECH:
				return modularReturn

		## Modular Python End
		## *******************

		return TechTypes.NO_TECH

	def canRazeCity(self,argsList):
		iRazingPlayer, pCity = argsList

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canRazeCity']:
			if not module.canRazeCity(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def canDeclareWar(self,argsList):
		iAttackingTeam, iDefendingTeam = argsList

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canDeclareWar']:
			if not module.canDeclareWar(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def skipProductionPopup(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['skipProductionPopup']:
			if module.skipProductionPopup(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def showExamineCityButton(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['showExamineCityButton']:
			if not module.showExamineCityButton(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def getRecommendedUnit(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getRecommendedUnit']:
			modularReturn = module.getRecommendedUnit(self, argsList)
			if modularReturn != UnitTypes.NO_UNIT:
				return modularReturn

		## Modular Python End
		## *******************

		return UnitTypes.NO_UNIT

	def getRecommendedBuilding(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getRecommendedBuilding']:
			modularReturn = module.getRecommendedBuilding(self, argsList)
			if modularReturn != BuildingTypes.NO_BUILDING:
				return modularReturn

		## Modular Python End
		## *******************

		return BuildingTypes.NO_BUILDING

	def updateColoredPlots(self):

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['updateColoredPlots']:
			if module.updateColoredPlots(self):
				return True

		## Modular Python End
		## *******************

		return False

	def isActionRecommended(self,argsList):
		pUnit = argsList[0]
		iAction = argsList[1]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['isActionRecommended']:
			if module.isActionRecommended(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def unitCannotMoveInto(self,argsList):
		ePlayer = argsList[0]
		iUnitId = argsList[1]
		iPlotX = argsList[2]
		iPlotY = argsList[3]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['unitCannotMoveInto']:
			if module.unitCannotMoveInto(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotHandleAction(self,argsList):
		pPlot = argsList[0]
		iAction = argsList[1]
		bTestVisible = argsList[2]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotHandleAction']:
			if module.cannotHandleAction(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def canBuild(self,argsList):
		iX, iY, iBuild, iPlayer = argsList
		gc 			= CyGlobalContext()
		getInfoType = gc.getInfoTypeForString
		pPlayer 	= gc.getPlayer(iPlayer)
		pTeam 		= gc.getTeam(pPlayer.getTeam())
		eCiv 		= pPlayer.getCivilizationType()
		Manager		= CvEventInterface.getEventManager()
		Civ			= Manager.Civilizations
		Improvement	= Manager.Improvements
		Build		= Manager.Builds
		Terrain 	= Manager.Terrain
		Bonus	 	= Manager.Resources

		if eCiv == Civ["Malakim"]:
			pPlot 	= CyMap().plot(iX, iY)
			if (iBuild == Improvement["Road"]):
				if (pPlot.getTerrainType() == Terrain["Desert"]):
					return 0
# scions start
		elif eCiv == Civ["Scions"]:
			pPlot = CyMap().plot(iX, iY)
			if pPlot.getOwner() == iPlayer:
				if pPlot.isCity() == False:
					if (iBuild == Build["Farm"]) and (pPlot.getImprovementType() != Improvement["Farm"]):
						if pPlot.getBonusType(-1) == Bonus["Wheat"]:  return 1
						elif pPlot.getBonusType(-1) == Bonus["Corn"]: return 1
						elif pPlot.getBonusType(-1) == Bonus["Rice"]: return 1
						else: return 0

					if pPlot.getImprovementType() != Improvement["Cottage (I)"]:
						if pPlot.getTerrainType() == Terrain["Desert"]:
							if (iBuild == Build["Cottage"]): return 1

		if pPlayer.isHuman() == False:
			Tech	 	= Manager.Techs
			Trait	 	= Manager.Traits
			Alignment 	= Manager.Alignments
			Mana		= Manager.Mana
			Civic		= Manager.Civics
			hasTech		= pTeam.isHasTech
			isCivic 	= pPlayer.isCivic
			hasBonus	= pPlayer.hasBonus
			eAlignment 	= pPlayer.getAlignment()

			if hasTech(Tech["Construction"]):
				if isCivic(Civic["Aristocracy"]) and isCivic(Civic["Agrarianism"]):
					if iBuild == Build["Cottage"]: return 0

			if isCivic(Civic["Arete"]):
				if iBuild == Build["Windmill"]: return 0

			if not hasTech(Tech["Guilds"]):
				if not pPlayer.hasTrait(Trait["Fallow"]):
					if iBuild == Build["Workshop"]: return 0

			if hasTech(Tech["Necromancy"]):
				if eAlignment == Alignment["Good"]:
					if iBuild == Build["Mana Death"]: 	return 0
					if iBuild == Build["Mana Entropy"]:	return 0
			if hasTech(Tech["Divination"]):
				if eAlignment == Alignment["Evil"]:
					if iBuild == Build["Mana Life"]: 	return 0
			# Waste for elven civs to build these
			if iBuild == Build["Lumbermill"]:
				if eCiv == Civ["Ljosalfar"] or eCiv == Civ["Svartalfar"]:
					return 0
			# Luchuirp need fire for blasting workshops, but only one
			if gc.getBuildInfo(iBuild).getType()[0:11] == 'BUILD_MANA_':
				if eCiv == Civ["Luchuirp"]:
					if hasTech(Tech["Elementalism"]):
						if not hasBonus(Mana["Fire"]):
							if iBuild != Build["Mana Fire"]:	return 0
				# Spectres!
				if eCiv in (Civ["Sheaim"], Civ["Calabim"], Civ["Balseraphs"]):
					hasHolyCity = pPlayer.hasHolyCity
					Rel			= Manager.Religions
					if iBuild not in (Build["Mana Death"], Build["Mana Chaos"], Build["Mana Entropy"], Build["Mana Shadow"], Build["Mana Enchantment"]):
						return 0
					if hasBonus(Mana["Chaos"]):
						if iBuild == Build["Mana Chaos"]:		return 0
					if hasBonus(Mana["Shadow"]) or hasHolyCity(Rel["Council of Esus"]):
						if iBuild == Build["Mana Shadow"]:		return 0
					if hasBonus(Mana["Entropy"]) or hasHolyCity(Rel["Ashen Veil"]):
						if iBuild == Build["Mana Entropy"]:		return 0
					if hasBonus(Mana["Enchantment"]):
						if iBuild == Build["Mana Enchantment"]:	return 0
				#one enchantment node for everyone
				if hasTech(Tech["Alteration"]):
					if not hasBonus(Mana["Enchantment"]):
						if iBuild != Build["Mana Enchantment"]:	return 0
					elif iBuild == Build["Mana Enchantment"]:	return 0
				#one life node for non evil civs
				if hasTech(Tech["Divination"]):
					if eAlignment != Alignment["Evil"]:
						if not hasBonus(Mana["Life"]):
							if iBuild != Build["Mana Life"]:	return 0
						elif iBuild == Build["Mana Life"]:		return 0
				#one fire node for elves
				if hasTech(Tech["Elementalism"]):
					if eCiv == Civ["Ljosalfar"] or eCiv == Civ["Svartalfar"]:
						if not hasBonus(Mana["Fire"]):
							if iBuild != Build["Mana Fire"]:	return 0
						elif iBuild == Build["Mana Fire"]:		return 0
				#one body node for most civs
				if hasTech(Tech["Alteration"]):
					if eCiv not in (Civ["Lanun"], Civ["Sheaim"], Civ["Luchuirp"], Civ["Scions"]):
						if not hasBonus(Mana["Body"]):
							if hasBonus(Mana["Enchantment"]):
								if iBuild != Build["Mana Body"]:	return 0
							elif iBuild == Build["Mana Body"]:		return 0
				#Evil civs take advantage of Necromancy
				if hasTech(Tech["Necromancy"]):
					if eAlignment == Alignment["Evil"]:
						if not hasBonus(Mana["Death"]):
							if iBuild != Build["Mana Death"]: return 0
						if hasBonus(Mana["Death"]):
							if not hasBonus(Mana["Entropy"]):
								if iBuild != Build["Mana Entropy"]:return 0

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canBuild']:
			modularReturn = module.canBuild(self, argsList)
			if modularReturn != -1:
				return modularReturn

		## Modular Python End
		## *******************

		return -1	# Returning -1 means ignore; 0 means Build cannot be performed; 1 or greater means it can

	def cannotFoundCity(self,argsList):
		#This python call has been turned off.
		#Settling on mana will remove the mana, as it used to.
		#The No Settlers option is now handled in the DLL.
		iPlayer, iPlotX, iPlotY = argsList
		gc = CyGlobalContext()
		pPlot = CyMap().plot(iPlotX,iPlotY)
		Manager		= CvEventInterface.getEventManager()
		Civ			= Manager.Civilizations
		Option		= Manager.GameOptions
		Resource	= Manager.Resources

# scions start
		pPlayer = gc.getPlayer(iPlayer)

		if Option["No Settlers"]:
			if pPlayer.getCivilizationType() == Civ["Scions"]:
				if pPlayer.getNumCities() > 0:
					return True
# scions end

		if pPlot.getBonusType(-1) == Resource["Mana"]:
			return True

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotFoundCity']:
			if module.cannotFoundCity(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotSelectionListMove(self,argsList):
		pPlot = argsList[0]
		bAlt = argsList[1]
		bShift = argsList[2]
		bCtrl = argsList[3]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotSelectionListMove']:
			if module.cannotSelectionListMove(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotSelectionListGameNetMessage(self,argsList):
		eMessage = argsList[0]
		iData2 = argsList[1]
		iData3 = argsList[2]
		iData4 = argsList[3]
		iFlags = argsList[4]
		bAlt = argsList[5]
		bShift = argsList[6]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotSelectionListGameNetMessage']:
			if module.cannotSelectionListGameNetMessage(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotDoControl(self,argsList):
		eControl = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotDoControl']:
			if module.cannotDoControl(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def canResearch(self,argsList):
		ePlayer = argsList[0]
		eTech = argsList[1]
		bTrade = argsList[2]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canResearch']:
			if module.canResearch(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotResearch(self,argsList):
		ePlayer 	= argsList[0]
		eTech 		= argsList[1]
		bTrade 		= argsList[2]
		gc 			= CyGlobalContext()
		pPlayer 	= gc.getPlayer(ePlayer)
		pTeam 		= gc.getTeam(pPlayer.getTeam())
		sf 			= ScenarioFunctions.ScenarioFunctions()
		Manager		= CvEventInterface.getEventManager()
		Civ			= Manager.Civilizations
		Trait		= Manager.Traits
		Alignment	= Manager.Alignments
		Unit		 = Manager.Units
		Tech		= Manager.Techs
		Option		= Manager.GameOptions
		hasTrait	= pPlayer.hasTrait
		eAlignment	= pPlayer.getAlignment()
		eCiv		= pPlayer.getCivilizationType()
		bAI			= pPlayer.isHuman() == False
		bAgnostic	= pPlayer.isAgnostic()

		if eTech == Tech["Orders from Heaven"]:
			if Option["No Order"]: return True
			if bAgnostic: return True
			if bAI and eAlignment == Alignment["Evil"]: return True

		elif eTech == Tech["White Hand"]:
			if bAgnostic: return True

		elif eTech == Tech["Way of the Earthmother"]:
			if Option["No RoK"]: return True
			if bAgnostic: return True

		elif eTech == Tech["Way of the Forests"]:
			if Option["No Leaves"]: return True
			if bAgnostic: return True

		elif eTech == Tech["Message from the Deep"]:
			if Option["No OO"]: return True
			if bAgnostic: return True
			if bAI and eAlignment == Alignment["Good"]: return True

		elif eTech == Tech["Corruption of Spirit"]:
			if Option["No Veil"]: return True
			if bAgnostic: return True
			if bAI and eAlignment == Alignment["Good"]: return True

		elif eTech == Tech["Way of the Wise"]:
			if bAI and eAlignment == Alignment["Evil"]: return True

		elif eTech == Tech["Way of the Wicked"]:
			if bAI and eAlignment == Alignment["Good"]: return True

		elif eTech == Tech["Honor"]:
			if bAgnostic: return True
			if bAI and eAlignment == Alignment["Evil"]: return True

		elif eTech == Tech["Deception"]:
			if bAgnostic: return True
			if bAI and eAlignment == Alignment["Good"]: return True

		elif eTech == Tech["Seafaring"]:
			if eCiv != Civ["Lanun"]: return True

		elif eTech == Tech["Steam Power"]:
			if eCiv != Civ["Mechanos"]: return True

		elif eTech == Tech["Alchemy"]:
			if eCiv != Civ["Mechanos"] and Unit["Generic"]["Wandering Sage"]==-1 : return True
			
		elif eTech == Tech["Swampdwelling"]:return True
		elif eTech == Tech["The Gift"]: return True

		if CyGame().getWBMapScript():
			bBlock = sf.cannotResearch(ePlayer, eTech, bTrade)
			if bBlock:
				return True

# Block techs in certain situations.
		if bAI:
			isHasTech 	= pTeam.isHasTech
			hasBonus	= pPlayer.hasBonus
			Bonus		= Manager.Resources
			Civic		= Manager.Civics
			isCivic 	= pPlayer.isCivic

			if eTech == Tech["Stirrups"]:
				if not isHasTech(Tech["Iron Working"]):
					if eCiv == Civ["Luchuirp"] or eCiv == Civ["Khazad"]:
						return True
				elif eCiv == Civ["Ljosalfar"]:
					if not hasBonus(Bonus["Deer"]):
						return True
				elif not hasBonus(Bonus["Horse"]):
					if not hasBonus(Bonus["Nightmare"]):
						if not hasBonus(Bonus["Camel"]):
							if not eCiv == Civ["Kuriotates"]:
								return True

			elif eTech == Tech["Bowyers"]:
				if eCiv == Civ["Luchuirp"] or eCiv == Civ["Khazad"]:
					if not isHasTech(Tech["Mithril Working"]):
						return True
				elif not hasBonus(Bonus["Iron"]):
					if not hasBonus(Bonus["Copper"]):
						if not eCiv == Civ["Ljosalfar"]:
							return True

			elif eTech == Tech["Construction"]:
				if eCiv == Civ["Ljosalfar"] or eCiv == Civ["Svartalfar"]:
					if not isHasTech(Tech["Sanitation"]):
						return True

##			elif eTech == Tech["Priesthood"]:
##				if not bAgnostic:
##					if pPlayer.getStateReligion() == -1:
##						if not eCiv == Civ["Mechanos"]:
##							return True

			elif eTech == Tech["Divination"]:
				if eAlignment == Alignment["Evil"]:
					if not isHasTech(Tech["Necromancy"]):
						return True

			elif eTech == Tech["Necromancy"]:
				if eAlignment == Alignment["Good"]:
					if not isHasTech(Tech["Divination"]):
						return True

# Once you have signed the Pact, there's no going back!.
			elif eTech == Tech["Way of the Forests"]:
				if isHasTech(Tech["Infernal Pact"]):
					if isCivic(Civic["Sacrifice The Weak"]): return True

			elif eTech == Tech["Honor"]:
				if isHasTech(Tech["Infernal Pact"]):
					if isCivic(Civic["Sacrifice The Weak"]): return True

			elif eTech == Tech["Orders from Heaven"]:
				if isHasTech(Tech["Infernal Pact"]):
					if isCivic(Civic["Sacrifice The Weak"]): return True

			elif eTech == Tech["Way of the Earthmother"]:
				if isHasTech(Tech["Infernal Pact"]):
					if isCivic(Civic["Sacrifice The Weak"]): return True

			elif eTech == Tech["Message from the Deep"]:
				if isHasTech(Tech["Infernal Pact"]):
					if isCivic(Civic["Sacrifice The Weak"]): return True

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotResearch']:
			if module.cannotResearch(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def canDoCivic(self,argsList):
		ePlayer = argsList[0]
		eCivic = argsList[1]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canDoCivic']:
			if module.canDoCivic(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotDoCivic(self,argsList):
		ePlayer 	= argsList[0]
		eCivic 		= argsList[1]
		gc 			= CyGlobalContext()
		pPlayer 	= gc.getPlayer(ePlayer)
		pTeam 		= gc.getTeam(pPlayer.getTeam())
		eCiv		= pPlayer.getCivilizationType()
		Manager		= CvEventInterface.getEventManager()
		Civ			= Manager.Civilizations
		Civic		= Manager.Civics
		eCivicType  = gc.getCivicInfo(eCivic).getCivicOptionType()

		if eCiv == Civ["Jotnar"]:
			if eCivicType == Civic["Government"]:
				if eCivic != Civic["Traditions"]:	return True

		if pPlayer.isHuman() == False:
			Trait 		= Manager.Traits
			UnitClass 	= Manager.UnitClasses
			Tech	 	= Manager.Techs
			hasTech		= pTeam.isHasTech
			isCivic 	= pPlayer.isCivic
			hasTrait	= pPlayer.hasTrait

			if   eCivic == Civic["Religion"]:
				if pPlayer.getStateReligion() == -1: return True

			elif eCivic == Civic["Pacifism"]:
				if not hasTrait(Trait["Philosophical"]):
					unitCCM = pPlayer.getUnitClassCountPlusMaking
					if unitCCM(UnitClass["Warrior"]) >= 5 and unitCCM(UnitClass["Archer"]) >= 5 and unitCCM(UnitClass["Axeman"]) >= 5:
						if pTeam.getAtWarCount(True) == 1:	return True

			elif eCivic == Civic["Conquest"]:
				if hasTrait(Trait["Fallow"]):		return True
				if hasTrait(Trait["Financial"]):	return True
				if not hasTech(Tech["Sanitation"]):	return True
				if pPlayer.getNumCities() <= 5: 	return True
				if isCivic(Civic["Aristocracy"]): 	return True

			elif eCivic == Civic["Tribalism"]:
				if hasTech(Tech["Education"]): 	  return True

			elif eCivic == Civic["Mercentalism"]: return True

			elif eCivic == Civic["Despotism"]:
				if hasTech(Tech["Cartography"]):  return True
				elif hasTech(Tech["Mysticism"]):  return True

			elif eCivic == Civic["God King"]:
				if hasTech(Tech["Cartography"]):
					if not eCiv == Civ["Kuriotates"]:
						if pPlayer.getNumCities() >= 6: return True

			elif eCivic == Civic["Apprenticeship"]:
				if hasTech(Tech["Taxation"]): return True
# Scions start
			elif eCivic == Civic["Slavery"]:
				if eCiv == Civ["Scions"]: return True
# scions end

			if hasTech(Tech["Taxation"]) or hasTech(Tech["Guilds"]):
				if not eCivic in(Civic["Caste System"], Civic["Arete"], Civic["Guilds"]):
					return True
			if hasTech(Tech["Trade"]):
				if hasTech(Tech["Sailing"]):
					if eCivicType == Civic["Economy"]:
						if eCivic != Civic["Guardian of Nature"]:
							if eCivic != Civic["Foreign Trade"]:
								if pPlayer.countNumCoastalCities() >=8:
									print ("Trade Economy")
									return True
			if hasTech(Tech["Warfare"]):
				if hasTech(Tech["Sanitation"]):
					if not hasTrait(Trait["Financial"]) :
						if not hasTrait(Trait["Fallow"]) :
							if eCivicType == Civic["Labor"]:
								if eCivic == Civic["Apprenticeship"] or eCivic == Civic["Caste System"]:
									if eCivicType == Civic["Economy"]:
										if eCivic != Civic["Conquest"] or eCivic != Civic["Guardian of Nature"] or eCivic != Civic["Foreign Trade"]:
											BCCPM = pPlayer.getBuildingClassCountPlusMaking
											if hasTrait(Trait["Aggressive"]) or hasTrait(Trait["Charismatic"]):
												print ("Conquest Forced due to Trait")
												return True
											if BCCPM(Building["Form of the Titan"])== 1:
												print ("Conquest Forced due to Form of The Titan")
												return True
											if hasTrait(Trait["Organized"])	and BCCPM(Building["Command Post"])>= 3:
												print ("Conquest Forced due to Command Posts")
												return True

			if hasTech(Tech["Code of Laws"]):
				if eCivicType == Civic["Government"]:
					if eCivic != Civic["Aristocracy"]:
						if hasTrait(Trait["Financial"]): return True
				elif isCivic(Civic["Aristocracy"]):
					if eCivicType == Civic["Economy"]:
						if hasTech(Tech["Calendar"]):
							if eCivic != Civic["Agrarianism"] or eCivic != Civic["Guardian of Nature"]:
								return True

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotDoCivic']:
			if module.cannotDoCivic(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def canTrain(self,argsList):
		pCity = argsList[0]
		eUnit = argsList[1]
		bContinue 		= argsList[2]
		bTestVisible 	= argsList[3]
		bIgnoreCost 	= argsList[4]
		bIgnoreUpgrades = argsList[5]
		gc 			= CyGlobalContext()
		ePlayer 	= pCity.getOwner()
		pPlayer 	= gc.getPlayer(ePlayer)
		eUnitClass 	= gc.getUnitInfo(eUnit).getUnitClassType()

		Manager		= CvEventInterface.getEventManager()
		UnitClass	= Manager.UnitClasses
		Building	= Manager.Buildings
		Civ			= Manager.Civilizations

		if Manager.GameOptions["One City Challenge"]:
			if pPlayer.getCivilizationType() == Civ["Scions"]:
				if eUnitClass == UnitClass["Awakened"]:
					if pCity.getNumRealBuilding(Building["Scions Palace"]) > 0:
						return True
				if eUnitClass == UnitClass["Reborn"]:
					if pCity.getNumRealBuilding(Building["Cathedral of Rebirth"]) > 0:
						return True

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canTrain']:
			if module.canTrain(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotTrain(self,argsList):
		pCity 			= argsList[0]
		eUnit 			= argsList[1]
		bContinue 		= argsList[2]
		bTestVisible 	= argsList[3]
		bIgnoreCost 	= argsList[4]
		bIgnoreUpgrades = argsList[5]
		gc 				= CyGlobalContext()
		ePlayer 		= pCity.getOwner()
		pPlayer 		= gc.getPlayer(ePlayer)
		eUnitClass 		= gc.getUnitInfo(eUnit).getUnitClassType()
		pTeam 			= gc.getTeam(pPlayer.getTeam())
		hasTech			= pTeam.isHasTech
		iStable 		= 0
		sf 				= ScenarioFunctions.ScenarioFunctions()
		canConstruct	= pPlayer.canConstruct
		getUCC			= pPlayer.getUnitClassCount
		eCiv			= pPlayer.getCivilizationType()
		bAI 			= not pPlayer.isHuman()
		iNumCities 		= pPlayer.getNumCities()
		getUCCPlusMaking= pPlayer.getUnitClassCountPlusMaking

		Manager		 	= CvEventInterface.getEventManager()
		UnitClass	 	= Manager.UnitClasses
		Tech		 	= Manager.Techs
		Hero		 	= Manager.Heroes
		Trait		 	= Manager.Traits
		Civ			 	= Manager.Civilizations
		Rel			 	= Manager.Religions
		Civic		 	= Manager.Civics
		Bonus		 	= Manager.Resources
		Leader		 	= Manager.Leaders
		Unit		 	= Manager.Units
		BuildingClass	= Manager.BuildingClasses
		Building	 	= Manager.Buildings
		bBarbarian		= pPlayer.isBarbarian()
		hasBonus		= pPlayer.hasBonus

		# if  bAI and not bContinue:
			# return False #attempt to stop ai python adhoc rules
			# infoCiv = gc.getCivilizationInfo(eCiv)
			# if eUnit == Unit["Bannor"]["Demagog"]:
				# if getUCC(UnitClass["Demagog"]) > 6: return True
			# # Units outdated? Dont build more - Hunters are limited elsewhere.
			# elif eUnit == Unit["Generic"]["Horseman"]:
				# if eCiv != Civ["Hippus"]:
					# iHorsemancounter = 0
					# for iTeam2 in range(gc.getMAX_PLAYERS()):
						# eTeam2 = gc.getTeam(iTeam2)
						# if eTeam2.isAlive():
							# isHasTech = eTeam2.isHasTech
							# if isHasTech(Tech["Iron Working"]): 	iHorsemancounter += 2
							# if isHasTech(Tech["Bowyers"]): 			iHorsemancounter += 2
							# if isHasTech(Tech["Stirrups"]): 		iHorsemancounter += 2
							# if isHasTech(Tech["Animal Handling"]): 	iHorsemancounter += 2
					# if hasBonus(Bonus["Iron"]):						iHorsemancounter += 2
					# if iHorsemancounter > 3:
						# if getUCC(UnitClass["Horseman"]) >= 5:
							# print ("Horseman Blocked")
							# return True

			# elif eUnit == Unit["Generic"]["Ranger"]:
				# if eCiv != Civ["Ljosalfar"] and eCiv != Civ["Svartalfar"]:
					# iRangercounter = 0
					# for iTeam2 in xrange(gc.getMAX_PLAYERS()):
						# eTeam2 = gc.getTeam(iTeam2)
						# if eTeam2.isAlive():
							# isHasTech = eTeam2.isHasTech
							# if isHasTech(Tech["Iron Working"]): 	iRangercounter += 2
							# if isHasTech(Tech["Bowyers"]): 			iRangercounter += 2
					# if hasTech(Tech["Iron Working"]):				iRangercounter += 2
					# if hasBonus(Bonus["Iron"]): 					iRangercounter += 2
					# if iRangercounter > 3:
						# if getUCC(UnitClass["Ranger"]) >= 30:
							# print ("Ranger Blocked")
							# return True

			# # don't go pirating if there are big ships hunting you
			# elif eUnit == Unit["Generic"]["Privateer"]:
				# iPrivateercounter = 0
				# for iTeam2 in xrange(gc.getMAX_PLAYERS()):
					# eTeam2 = gc.getTeam(iTeam2)
					# if eTeam2.isAlive():
						# isHasTech = eTeam2.isHasTech
						# if isHasTech(Tech["Optics"]) and isHasTech(Tech["Iron Working"]):
							# iPrivateercounter = iPrivateercounter +1
				# if iPrivateercounter > 1: return True

			# elif eUnit == Unit["Generic"]["Javelin Thrower"]:
				# if 2 * iNumCities <= getUCCPlusMaking(UnitClass["Archer"]):
					# if hasTech(Tech["Bronze Working"]): return True

			# # UnitClasses
			# elif eUnitClass == UnitClass["Scout"]:
				# if eCiv != Civ["Svartalfar"] and eCiv != gc.getInfoTypeForString("CIVILIZATION_GOBLIN"):
					# if getUCC(UnitClass["Scout"]) > 3: return True
					# iHuntingLodge = infoCiv.getCivilizationBuildings(BuildingClass["Hunting Lodge"])
					# if iHuntingLodge != -1:
						# if canConstruct(iHuntingLodge, False, False, False, False): return True
			# # Settlers
			# elif eUnitClass == UnitClass["Settler"]:

				# if iNumCities > 3:
					# if not (hasTech(Tech["Code of Laws"]) and hasTech(Tech["Festivals"]) and hasTech(Tech["Cartography"])): return True

				# if iNumCities <= 5:
					# if not hasTech(Tech["Festivals"]) and not hasTech(Tech["Cartography"]):
						# if getUCCPlusMaking(UnitClass["Settler"]) > 1: return True
				# else:
					# if getUCCPlusMaking(UnitClass["Settler"]) > 2: return True


			# # Dont spam too many priests
			# elif eUnitClass == UnitClass["Priest of Leaves"]:
				# if 3* iNumCities <= getUCCPlusMaking(UnitClass["Priest of Leaves"]) :
					# if not hasTech(Tech["Theology"]): return True
			# elif eUnitClass == UnitClass["Priest of Kilmorph"]:
				# if 3* iNumCities <= getUCCPlusMaking(UnitClass["Priest of Kilmorph"]) :
					# if not hasTech(Tech["Theology"]): return True
			# elif eUnitClass == UnitClass["Priest of Order"]:
				# if 5* iNumCities <= getUCCPlusMaking(UnitClass["Priest of Order"]) :
					# if not hasTech(Tech["Theology"]): return True
			# elif eUnitClass == UnitClass["Priest of Empyrean"]:
				# if 5* iNumCities <= getUCCPlusMaking(UnitClass["Priest of Empyrean"]) :
					# if not hasTech(Tech["Theology"]): return True
			# elif eUnitClass == UnitClass["Priest of Overlords"]:
				# if 5* iNumCities <= getUCCPlusMaking(UnitClass["Priest of Overlords"]) :
					# if not hasTech(Tech["Theology"]): return True
			# elif eUnitClass == UnitClass["Priest of Veil"]:
				# if 5* iNumCities <= getUCCPlusMaking(UnitClass["Priest of Veil"]) :
					# if not hasTech(Tech["Theology"]): return True

			# elif eUnitClass == UnitClass["Hunter"]:
				# if eCiv != Civ["Svartalfar"]:
					# if hasTech(Tech["Bronze Working"]) and hasBonus(Bonus["Copper"]):
						# if 2* iNumCities <= getUCCPlusMaking(UnitClass["Hunter"]): return True

			# elif eUnitClass == UnitClass["Worker"]:
				# if pTeam.getAtWarCount(True) > 0:
					# if getUCCPlusMaking(UnitClass["Worker"]) > iNumCities:	return True
				# if getUCCPlusMaking(UnitClass["Worker"]) > (iNumCities * 3):return True
				# if pCity.isCapital():
					# iNumDefenders = 0
					# iNumDefenders += getUCC(UnitClass["Warrior"])
					# iNumDefenders += getUCC(UnitClass["Archer"])
					# iNumDefenders += getUCC(UnitClass["Axeman"])
					# iNumDefenders += getUCC(UnitClass["Longbowman"])
					# iDefRequired = 3.5 + (getUCC(UnitClass["Worker"]) * 1.5)
					# if iNumDefenders < iDefRequired: return True
				# else:
					# iMinSize = 3
					# if eCiv == Civ["Luchuirp"]: iMinSize = 1;
					# if pCity.getPopulation() <	iMinSize: return True
					# iNumDefenders = 0
					# iNumDefenders += getUCCPlusMaking(UnitClass["Warrior"])
					# iNumDefenders += getUCCPlusMaking(UnitClass["Archer"])
					# iNumDefenders += getUCCPlusMaking(UnitClass["Axeman"])
					# iNumDefenders += getUCCPlusMaking(UnitClass["Longbowman"])
					# if iNumDefenders < (iNumCities * 3):	return True

			# elif eUnitClass == Hero["Class-Rantine"]:
				# if not pCity.isCapital():	return True

			# elif eUnitClass == UnitClass["Disciple Empyrean"]:
				# if getUCC(UnitClass["Disciple Empyrean"]) > 2:	return True
				# if not pPlayer.hasHolyCity(Rel["Empyrean"]):
					# if not eCiv == Civ["Malakim"]:			return True
			# elif eUnitClass == UnitClass["Disciple Leaves"]:
				# if getUCC(UnitClass["Disciple Leaves"]) > 2:	return True
				# if not pPlayer.hasHolyCity(Rel["Fellowship"]) :
					# if not eCiv == Civ["Ljosalfar"]:		return True
			# elif eUnitClass == UnitClass["Disciple Overlords"]:
				# if getUCC(UnitClass["Disciple Overlords"]) > 2:	return True
				# if not pPlayer.hasHolyCity(Rel["Octopus Overlords"]) :
					# if not eCiv == Civ["Lanun"]:			return True
			# elif eUnitClass == UnitClass["Disciple Kilmorph"]:
				# if getUCC(UnitClass["Disciple Kilmorph"]) > 2:	return True
				# if not pPlayer.hasHolyCity(Rel["Runes of Kilmorph"]) :
					# if not eCiv == Civ["Khazad"]:			return True
			# elif eUnitClass == UnitClass["Disciple Veil"]:
				# if getUCC(UnitClass["Disciple Veil"]) > 2: return True
				# if not pPlayer.hasHolyCity(Rel["Ashen Veil"]) :
					# if not eCiv == Civ["Sheaim"]:			return True
			# elif eUnitClass == UnitClass["Disciple Order"]:
				# if getUCC(UnitClass["Disciple Order"]) > 2:	return True
				# if not pPlayer.hasHolyCity(Rel["Order"]) :
					# if not eCiv == Civ["Bannor"]:			return True

			# # don't start producing units that need to be finished fast in backwater cities
			# if isWorldUnitClass(eUnitClass):
				# if pCity.findBaseYieldRateRank(YieldTypes.YIELD_PRODUCTION)>2 and not bBarbarian:
					# if pCity.getUnitProduction(eUnit) == 0: return True

		# LIMITATIONS FOR BOTH AI AND HUMAN PLAYERS - BEGINNING
		if pPlayer.isCivic(Civic["Crusade"]):
			if eUnit == Unit["Generic"]["Worker"]: 		return True
			if eUnit == Unit["Generic"]["Settler"]: 	return True
			if eUnit == Unit["Generic"]["Workboat"]: 	return True

		if eUnit == Unit["Veil"]["Beast of Agares"]:
			if pCity.getPopulation() <= 5: return True
		elif eUnit == Unit["Cualli"]["Shadow Priest of Agruonn"]:
			if not CyGame().isUnitClassMaxedOut(Hero["Class-Miquiztli"], 0): return True
		elif eUnit == Hero["Acheron"]:
			if Manager.GameOptions["No Acheron"]: return True
		elif eUnit == Hero["Duin"]:
			if Manager.GameOptions["No Duin"]: return True
			for iPlayer in xrange(gc.getMAX_PLAYERS()):
				pLoopPlayer = gc.getPlayer(iPlayer)
				if pLoopPlayer.getLeaderType() == Leader["Duin"] and pLoopPlayer.isAlive(): return True
		elif eUnit == Hero["Varulv"]:
			if pPlayer.getLeaderType() != Leader["Duin"]: return True
		#elif eUnit == Unit["Summons"]["Water Elemental"]:
		#	if not pPlayer.hasTrait(Trait["Hydromancer 2"]): return True
	#	elif eUnit == gc.getInfoTypeForString("UNIT_PRIESTESS_OF_BHALL") and pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC")) and pPlayer.getCivilizationType()==gc.getInfoTypeForString("CIVILIZATION_CUALLI"):
	#		if not pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC2")):
	#			return True
	#	elif eUnit == gc.getInfoTypeForString("UNIT_LIZARD_PRIEST_OF_AGRUONN") and pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC")) and pPlayer.getCivilizationType()==gc.getInfoTypeForString("CIVILIZATION_CLAN_OF_EMBERS"):
	#		if not pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC2")):
	#			return True
	#	elif eUnit == gc.getInfoTypeForString("UNIT_HIGH_PRIESTESS_OF_BHALL") and pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC")) and pPlayer.getCivilizationType()==gc.getInfoTypeForString("CIVILIZATION_CUALLI"):
	#		if not pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC3")):
	#			return True
	#	elif eUnit == gc.getInfoTypeForString("UNIT_SHADOW_PRIEST_OF_AGRUONN") and pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC")) and pPlayer.getCivilizationType()==gc.getInfoTypeForString("CIVILIZATION_CLAN_OF_EMBERS"):
	#		if not pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_HEMAPYROSYNCRETISTIC3")):
	#			return True
	#	elif eUnit == Hero["Kahd"]:
	#		if not (pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_KAHD_OGHMA")) or pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_KAHD_MAMMON"))):	return True

		# emergency warrior production. # Note from Ronkhar : this would be bad when we enable Dtesh AI
		#if bAI:
		#	if eUnitClass != UnitClass["Warrior"]:
		#		if pPlayer.getUnitClassCountPlusMaking(UnitClass["Warrior"]) <= 2:
		#			if not hasTech(Tech["Bronze Working"]) and not hasTech(Tech["Archery"]): return True


		if CyGame().getWBMapScript():
			bBlock = sf.cannotTrain(pCity, eUnit, bContinue, bTestVisible, bIgnoreCost, bIgnoreUpgrades)
			if bBlock:	return True

		if eCiv == Civ["Malakim"]:
			if pCity.getNumRealBuilding(Building["Camel Stable"]) > 0:	iStable = 1
			elif pCity.getNumRealBuilding(Building["Stable"]) > 0: 		iStable = 1
			if eUnit == Unit["Malakim"]["Horseman"]:
				if iStable == 0:	return True
			if eUnit == Unit["Malakim"]["Knight"]:
				if iStable == 0:	return True
			if eUnit == Unit["Malakim"]["Camel Archer"]:
				if iStable == 0: 	return True

		# Mekara Units
		# if eCiv != gc.getInfoTypeForString('CIVILIZATION_MEKARA'): #Ronkhar does not see any use to these 3 lines
		#	if eUnitClass == gc.getInfoTypeForString('UNIT_OVERSEER'): return True
		#	if eUnitClass == gc.getInfoTypeForString('UNIT_COMBAT_OVERSEER'): return True
		# TODO Ronkhar: redo all this limitation code
		#if pPlayer.getLeaderType() == gc.getInfoTypeForString('LEADER_ZARIA'):
		#	if eUnitClass == gc.getInfoTypeForString('UNITCLASS_ASSASSIN'): return True
		#	if eUnitClass == gc.getInfoTypeForString('UNITCLASS_SHADOW'): return True
		#else:
		#	if eUnitClass == gc.getInfoTypeForString('UNITCLASS_AGENT'): return True
		#	if eUnitClass == gc.getInfoTypeForString('UNITCLASS_ADJUNCT'): return True
		#	if eUnitClass == gc.getInfoTypeForString('UNITCLASS_CARETAKER_MATRON'): return True
	#	if pPlayer.getLeaderType() != gc.getInfoTypeForString('LEADER_JAMAL'):
	#		if eUnitClass == gc.getInfoTypeForString('UNITCLASS_KARAS_V2'): return True
		#if pPlayer.getLeaderType() != gc.getInfoTypeForString('LEADER_IRAM'):
		#	if eUnit == gc.getInfoTypeForString('UNIT_CUSTODIAN'): return True
		#	if eUnit == gc.getInfoTypeForString('UNIT_SHARPSHOOTER'): return True
		#	if eUnit == gc.getInfoTypeForString('UNIT_SKIRMISHER'): return True

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['cannotTrain']:
			if module.cannotTrain(self, argsList) == True:
				return True

		## Modular Python End
		## *******************

		return False

	def canConstruct(self,argsList):
		pCity = argsList[0]
		eBuilding = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		bIgnoreCost = argsList[4]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canConstruct']:
			if module.canConstruct(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotConstruct(self,argsList):
		pCity 			= argsList[0]
		eBuilding 		= argsList[1]
		bContinue 		= argsList[2]
		bTestVisible 	= argsList[3]
		bIgnoreCost 	= argsList[4]
		gc 				= CyGlobalContext()
		pPlayer 		= gc.getPlayer(pCity.getOwner())
		iBuildingClass 	= gc.getBuildingInfo(eBuilding).getBuildingClassType()
		bAI				= pPlayer.isHuman() == False
		pTeam 			= gc.getTeam(pPlayer.getTeam())
		eCiv 			= pPlayer.getCivilizationType()
		isCivic			= pPlayer.isCivic
		hasTrait		= pPlayer.hasTrait
		iNumCities		= pPlayer.getNumCities()
		bBarbarian		= pPlayer.isBarbarian()
		getNumB			= pCity.getNumBuilding

		Manager			= CvEventInterface.getEventManager()
		Civ				= Manager.Civilizations
		Rel				= Manager.Religions
		Leader			= Manager.Leaders
		UnitClass		= Manager.UnitClasses
		Tech			= Manager.Techs
		Trait			= Manager.Traits
		Building		= Manager.Buildings
		BuildingClass	= Manager.BuildingClasses
		Civic			= Manager.Civics
		Alignment		= Manager.Alignments
		Option			= Manager.GameOptions

		#if bAI:
		#	return False #attempt to stop ai python adhoc rules
		#	if pPlayer.getUnitClassCountPlusMaking(UnitClass["Warrior"]) <= 3:
		#		if not pTeam.isHasTech(Tech["Bronze Working"]):
		#			if not pTeam.isHasTech(Tech["Archery"]): return True

		#	if isWorldWonderClass(iBuildingClass):
		#		if pCity.findBaseYieldRateRank(YieldTypes.YIELD_PRODUCTION)>5 and not bBarbarian:
		#			if pCity.getBuildingProduction(eBuilding)==0: return True

		# """ Alchemy Lab """
		if   eBuilding == Building["Alchemy Lab"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Aqueduct """
		elif eBuilding == Building["Aqueduct"]:
			if isCivic(Civic["Crusade"]): return True
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if eCiv == Civ["Infernal"]: return True
			#	if pCity.badHealth(False)-pCity.goodHealth() < -1 : return True
			#	if pTeam.getAtWarCount(True) >= 1: return True

		# """ Archery Range """
		#elif Building == Building["Archery Range"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if iNumCities >= 3:
		#			if pPlayer.getBuildingClassCountPlusMaking(BuildingClass["Archery Range"]) * 3 >  iNumCities:
		#				if eCiv not in (Civ["Ljosalfar"], Civ["Sheaim"], Civ["Svartalfar"]):
		#					return True
		# """ Brewery """
		elif eBuilding == Building["Brewery"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Breeding Pit """
		#elif eBuilding == Building["Breeding Pit"]:
			#if bAI:
				
		#		return False #attempt to stop ai python adhoc rules
		#		if pCity.happyLevel() - pCity.unhappyLevel(1) <= 0: return True

		# """ Carnival """
		elif eBuilding == Building["Carnival"]:
			if isCivic(Civic["Crusade"]): return True
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if not hasTrait(Trait["Creative"]) :
			#		if pCity.happyLevel() - pCity.unhappyLevel(1) > 0: return True

		# """ Camel Stable """
		elif eBuilding == Building["Camel Stable"]:
			if eCiv == Civ["Malakim"]:
				if getNumB(Building["Stable"]) > 0: return True

		# """ City of a Thousand Slums """
		#elif eBuilding == Building["Thousand Slums"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if pCity.getPopulation() <=20: return True

		# """ Courthouse """
		elif eBuilding == Building["Courthouse"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Elder Council """
		elif eBuilding == Building["Elder Council"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Gambling House """
		elif eBuilding == Building["Gambling House"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Granary """
		elif eBuilding == Building["Granary"]:
			if isCivic(Civic["Crusade"]): return True
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if eCiv == Civ["Infernal"]: return True

		# """ Harbor """
		elif eBuilding == Building["Harbor"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Herbalist """
		elif eBuilding == Building["Herbalist"]:
			if isCivic(Civic["Crusade"]): return True
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if eCiv == Civ["Infernal"]: return True
			#	if pCity.badHealth(False)-pCity.goodHealth() < -1: return True

		# """ Hunting Lodge """
		#elif eBuilding == Building["Hunting Lodge"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if iNumCities >= 3:
		#			if pPlayer.getBuildingClassCountPlusMaking(BuildingClass["Hunting Lodge"]) * 3 > iNumCities:
		#				if eCiv != Civ["Svartalfar"]: return True

		# """ Imperial Cenotaph """
		elif eBuilding == Building["Imperial Cenotaph"]:
			if pPlayer.getLeaderType() == Leader["Risen Emperor"]: return True

		# """ Infirmary """
		#elif eBuilding == Building["Infirmary"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if eCiv == Civ["Infernal"]: return True
		#		if pCity.badHealth(False)-pCity.goodHealth() < 1: return True
		#		if pTeam.getAtWarCount(True) >= 1: return True

		# """ Inn """
		#elif eBuilding == Building["Inn"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if pCity.getPopulation() <=10: return True
		#		if pTeam.getAtWarCount(True) >= 1: return True

		# """ Library """
		elif eBuilding == Building["Library"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Market """
		elif eBuilding == Building["Market"]:
			if isCivic(Civic["Crusade"]): return True

		# """ Mercurian Gate """
		elif eBuilding == Building["Mercurian Gate"]:
			if Option["No Hyborem or Basium"]: return True
			if pPlayer.getStateReligion() == Rel["Ashen Veil"]: return True
			if pCity.isCapital() and not pCity.getCivilizationType() == Civ["Mercurians"]:
				return True
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if pPlayer.getAlignment() == Alignment["Evil"]: return True

		# """ Moneychanger """
		elif eBuilding == Building["Moneychanger"]:
			if isCivic(Civic["Crusade"]): return True

##		# """ Monument """
##		elif eBuilding == Building["Monument"]:
##			if isCivic(Civic["Crusade"]): return True
##			if bAI:
##				if hasTrait(Trait["Creative"]) and pCity.getPopulation() <=5:
##					return True
##				if not hasTrait(Trait["Financial"]):
##					if pCity.getPopulation() <=8: 		return True
##					if pTeam.getAtWarCount(True) >= 1:	return True

		# """ Monument to Avarice """
		elif eBuilding == Building["Monument to Avarice"]:
			if pPlayer.isFeatAccomplished(FeatTypes.FEAT_GLOBAL_SPELL):
				if hasTrait(gc.getInfoTypeForString("TRAIT_KAHD_MAMMON")): return False
			return True

		# """ Prophecy of Ragnarok """
		#elif eBuilding == Building["Prophechy of Ragnarok"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if pPlayer.getAlignment() != Alignment["Evil"]:
		#			return True

		# """ Public Baths """
		elif eBuilding == Building["Public Baths"]:
			if isCivic(Civic["Crusade"]): return True
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if eCiv == Civ["Infernal"]: return True

		# """ Reliquary """
		#if eBuilding == Building["Reliquary"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if pCity.getPopulation() <=8: return True

		# """ Sewer """
		#elif eBuilding == Building["Sewer"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if eCiv == Civ["Infernal"]: return True

		# """ Shrine of the Champion """
		elif eBuilding == Building["Shrine of the Champion"]:
			iHero = Manager.cf.getHero(pPlayer)
			if iHero == -1: return True
			if CyGame().isUnitClassMaxedOut(iHero, 0) == False: return True
			if pPlayer.getUnitClassCount(iHero) > 0: return True

		# """ Siege Workshop """
		elif eBuilding == Building["Siege Workshop"]:
			if not eCiv != Civ["Ljosalfar"]:	return True
			if not eCiv != Civ["Svartalfar"]:	return True
			if not pTeam.isHasTech(Tech["Construction"]): 	return True

		# """ Smokehouse """
		elif eBuilding == Building["Smokehouse"]:
			if isCivic(Civic["Crusade"]): return True
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if eCiv == Civ["Infernal"]: return True

		# """ Smugglers Port """
		elif eBuilding == Building["Smugglers Port"]:
			if pPlayer.isSmugglingRing() == False: return True

		# """ Stable """
		elif eBuilding == Building["Stable"]:
			#if bAI:
			#	return False #attempt to stop ai python adhoc rules
			#	if iNumCities >= 3:
			#		if pPlayer.getBuildingClassCountPlusMaking(BuildingClass["Stable"]) * 3 > iNumCities:
			#			if eCiv != Civ["Hippus"]: return True

			if eCiv == Civ["Malakim"]:
				if pCity.getNumBuilding(Building["Camel Stable"]) > 0: return True

		# """ Tavern """
		#if eBuilding == Building["Tavern"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if pCity.getPopulation() <=15:
		#			return True

		# """ Tax Office """
		#elif eBuilding == Building["Tax Office"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if pCity.getPopulation() <=12 or pCity.happyLevel() - pCity.unhappyLevel(1) <=0:
		#			return True
		#		if pTeam.getAtWarCount(True) >= 1: return True

		# """ Temple of the Gift """
		elif eBuilding == Building["Temple of the Gift"]:
			if pPlayer.getLeaderType() == Leader["Korrina"]: return True

		# """ Tower of Complacency """
		#elif 	eBuilding == Building["Tower of Complacency"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if pCity.goodHealth() <= 14: return True

		# """ Theatre """
		elif eBuilding == Building["Theatre"]:
			if isCivic(Civic["Crusade"]): return True
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if hasTrait(Trait["Creative"]) and pCity.getPopulation() <=6:
		#			return True
		#		if pTeam.getAtWarCount(True) >= 1:
		#			return True
		#		if hasTrait(Trait["Creative"]) == False:
		#			if pCity.getPopulation() <=12:
		#				return True

		# """ Training Yard """
		#elif eBuilding == Building["Training Yard"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if iNumCities >= 3:
		#			if eCiv == Civ["Svartalfar"] or eCiv == Civ["Hippus"] or eCiv == Civ["Ljosalfar"]:
		#				if pPlayer.getBuildingClassCountPlusMaking(BuildingClass["Training Yard"]) * 3 > iNumCities:
		#					return True

		# """ Vacant Mausoleum """
		elif eBuilding == Building["Vacant Mausoleum"]:
			if pPlayer.getLeaderType() == Leader["Risen Emperor"]: return True

		# """ Vault Gate """
		elif eBuilding == Building["Kahdi Vault Gate"]:
			if pPlayer.getLeaderType() != Leader["Kahd"]: return True

		# """ Well """
		#elif eBuilding == Building["Well"]:
		#	if bAI:
		#		return False #attempt to stop ai python adhoc rules
		#		if eCiv == Civ["Infernal"]: return True

		elif eBuilding == gc.getInfoTypeForString("BUILDING_RIDE_OF_THE_NINE_KINGS"):
			if not (pCity.hasBonus(gc.getInfoTypeForString("BONUS_HYAPON")) or pCity.hasBonus(gc.getInfoTypeForString("BONUS_HORSE")) or pCity.hasBonus(gc.getInfoTypeForString("BONUS_NIGHTMARE"))): return True

		iAltar1 = Building["Altar of Luonnotar"]
		iAltar2 = Building["Altar - Anointed"]
		iAltar3 = Building["Altar - Blessed"]
		iAltar4 = Building["Altar - Consecrated"]
		iAltar5 = Building["Altar - Divine"]
		iAltar6 = Building["Altar - Exalted"]
		iAltar7 = Building["Altar - Final"]

		if eBuilding in (iAltar1, iAltar2, iAltar3, iAltar4, iAltar5, iAltar6, iAltar7):
			if pPlayer.getAlignment() == Alignment["Evil"]: return True
			countNum = pPlayer.countNumBuildings
			if eBuilding == iAltar1:
				if (countNum(iAltar2) > 0 or countNum(iAltar3) > 0 or countNum(iAltar4) > 0 or countNum(iAltar5) > 0 or countNum(iAltar6) > 0 or countNum(iAltar7) > 0): return True
			elif eBuilding == iAltar2:
				if (countNum(iAltar3) > 0 or countNum(iAltar4) > 0 or countNum(iAltar5) > 0 or countNum(iAltar6) > 0 or countNum(iAltar7) > 0): return True
			elif eBuilding == iAltar3:
				if (countNum(iAltar4) > 0 or countNum(iAltar5) > 0 or countNum(iAltar6) > 0 or countNum(iAltar7) > 0): return True
			elif eBuilding == iAltar4:
				if (countNum(iAltar5) > 0 or countNum(iAltar6) > 0 or countNum(iAltar7) > 0): return True
			elif eBuilding == iAltar5:
				if (countNum(iAltar6) > 0 or countNum(iAltar7) > 0): return True
			elif eBuilding == iAltar6:
				if countNum(iAltar7) > 0: return True
				
				
		getInfoType			= gc.getInfoTypeForString
				
		if (getInfoType("MODULE_DAO")!=-1):
			if (eBuilding==getInfoType("BUILDING_SHRINE_AIR")):
				if pCity.getNumBuilding(getInfoType("BUILDING_SHRINE_EARTH"))>0:
					return True
			if (eBuilding==getInfoType("BUILDING_SHRINE_EARTH")):
				if pCity.getNumBuilding(getInfoType("BUILDING_SHRINE_AIR"))>0:
					return True
			if (eBuilding==getInfoType("BUILDING_SHRINE_WATER")):
				if pCity.getNumBuilding(getInfoType("BUILDING_SHRINE_FIRE"))>0:
					return True
			if (eBuilding==getInfoType("BUILDING_SHRINE_FIRE")):
				if pCity.getNumBuilding(getInfoType("BUILDING_SHRINE_WATER"))>0:
					return True
					
		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotConstruct']:
			if module.cannotConstruct(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def canCreate(self,argsList):
		pCity = argsList[0]
		eProject = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canCreate']:
			if module.canCreate(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotCreate(self,argsList):
		pCity = argsList[0]
		eProject = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		gc 				= CyGlobalContext()
		pPlayer 		= gc.getPlayer(pCity.getOwner())
		pTeam 			= gc.getTeam(pPlayer.getTeam())
		bAI 			= pPlayer.isHuman() == False
		eCiv			= pPlayer.getCivilizationType()

		Manager			= CvEventInterface.getEventManager()
		Civ				= Manager.Civilizations
		Alignment		= Manager.Alignments
		Rel				= Manager.Religions
		Project			= Manager.Projects
		Hero			= Manager.Heroes
		Leader			= Manager.Leaders
		Option			= Manager.GameOptions

	#	if bAI:
	#		#attempt to stop ai python adhoc rules
	#		if pCity.findBaseYieldRateRank(YieldTypes.YIELD_PRODUCTION)>2: return True

		if eProject == Project["Purge the Unfaithful"]:
			if not pPlayer.isHuman(): return True # this means AIs never cast this ritual. (even if they're aiming for religious victory) TODO update AI
			if pPlayer.getStateReligion() == -1: return True

		elif eProject == Project["Birthright Regained"]:
			if not pPlayer.isFeatAccomplished(FeatTypes.FEAT_GLOBAL_SPELL): return True

		elif eProject == Project["Stir From Slumber"]:
			if (pPlayer.getPlayersKilled() == 0 or pPlayer.getStateReligion() != Rel["White Hand"]):
					return True

		elif eProject == Project["The Deepening"]:
			if pPlayer.getStateReligion() != Rel["White Hand"]: return True

		elif eProject == Project["The Draw"]:
			if pPlayer.getLeaderType() == Leader["Raitlor"]: return True
			if bAI and pPlayer.getUnitClassCount(gc.getInfoTypeForString("UNITCLASS_AURIC"))==0 and pPlayer.getUnitClassCount(gc.getInfoTypeForString("UNITCLASS_AURIC_WINTER"))==0:
				return True

		elif eProject == Project["Ascension"]:
			if pPlayer.getLeaderType() == Leader["Raitlor"]: return True
			if eCiv == Civ["Illians"]:
				if pPlayer.getCivCounterMod() != 0: return True # Illian counter is 100 if Auric is dead

# TODO Ronkhar: split and move to frozen module (here = if genesis and civ illians. In module = if genesis and civ frozen)
		# """ Genesis """
		elif eProject == Project["Genesis"]:															#Changed in Frozen: TC01
			if eCiv in (Civ["Illians"], Civ["Frozen"]): return True

# TODO Ronkhar: move liberation to frozen module
		elif eProject == Project["Liberation"]:
			if Option["No Liberation"]: return True
			if pPlayer.getAlignment() == Alignment["Good"]: return True

		elif eProject == Project["Pax Diabolis"]:
			if pPlayer.getStateReligion() != Rel["Ashen Veil"] or not gc.getTeam(pPlayer.getTeam()).isAtWar(gc.getDEMON_TEAM()):
				return True
			if bAI and (pCity.getPopulation()>10 or pCity.isCapital() or pCity.isHolyCity()):
				return True
		elif eProject == Project["Prepare Expedition"]:
			if pPlayer.isFeatAccomplished(FeatTypes.FEAT_EXPEDITION_READY): return True

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotCreate']:
			if module.cannotCreate(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def canMaintain(self,argsList):
		pCity = argsList[0]
		eProcess = argsList[1]
		bContinue = argsList[2]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canMaintain']:
			if module.canMaintain(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotMaintain(self,argsList):
		pCity 		= argsList[0]
		eProcess 	= argsList[1]
		bContinue 	= argsList[2]
		gc 			= CyGlobalContext()
		pPlayer	 	= gc.getPlayer(pCity.getOwner())

		Manager		= CvEventInterface.getEventManager()
		Tech		= Manager.Techs
		Process		= Manager.Processes
		Civic		= Manager.Civics
		Building	= Manager.Buildings

		# Caste System Requires the civic
		if eProcess == Process["Caste System"] :
			if not pPlayer.isCivic(Civic["Caste System"]): return True

		# Wealth is automatically upgraded with the Taxation technology
		if eProcess == Process["Wealth"]:
			if gc.getTeam(pPlayer.getTeam()).isHasTech(Tech["Taxation"]): return True

		# Culture rate improved by running Liberty
		if eProcess == Process["Culture Improved"]:
			if not pPlayer.isCivic(Civic["Liberty"]): return True

		if eProcess == Process["Culture"]:
			if pPlayer.isCivic(Civic["Liberty"]): return True

		# Research rate conversion more effective with Academy
		if eProcess == Process["Research"]:
			if pCity.getNumRealBuilding(Building["Academy"]) > 0: return True

		if eProcess == Process["Research Improved"]:
			if not pCity.getNumRealBuilding(Building["Academy"]) > 0: return True

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotMaintain']:
			if module.cannotMaintain(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def AI_chooseTech(self,argsList):
		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['AI_chooseTech']:
			modularReturn = module.AI_chooseTech(self, argsList)
			if modularReturn != TechTypes.NO_TECH:
				return modularReturn

		## Modular Python End
		## *******************

		return TechTypes.NO_TECH

	def AI_chooseProduction(self,argsList):
		pCity 				= argsList[0]
		gc 					= CyGlobalContext()
		getInfoType			= gc.getInfoTypeForString
		game				= CyGame()
		eConstruct			= OrderTypes.ORDER_CONSTRUCT
		eTrain				= OrderTypes.ORDER_TRAIN
		iOwner				= pCity.getOwner()
		pPlayer 			= gc.getPlayer(iOwner)
		pTeam 				= gc.getTeam(pPlayer.getTeam())
		eCiv 				= pPlayer.getCivilizationType()
		eAlignment			= pPlayer.getAlignment()
		eRel				= pPlayer.getStateReligion()
		infoCiv 			= gc.getCivilizationInfo(eCiv)
		pPlot 				= pCity.plot()
		getNumB				= pCity.getNumBuilding
		canConstruct		= pCity.canConstruct
		getBCCPM			= pPlayer.getBuildingClassCountPlusMaking
		getUCCPM			= pPlayer.getUnitClassCountPlusMaking
		hasTrait			= pPlayer.hasTrait
		hasTech 			= pTeam.isHasTech
		getBaseYieldRate	= pCity.getBaseYieldRate
		iProductionRank 	= pCity.findBaseYieldRateRank(YieldTypes.YIELD_PRODUCTION)

		hasBonus			= pPlayer.hasBonus
		pushOrder			= pCity.pushOrder
		iWarCount			= pTeam.getAtWarCount(True)

		iGold				= pPlayer.getGold()
		isCivic				= pPlayer.isCivic
		hasHolyCity			= pPlayer.hasHolyCity
		isHolyCity			= pCity.isHolyCityByType
		randNum				= game.getSorenRandNum
		civB				= gc.getCivilizationInfo(eCiv).getCivilizationBuildings

		bAgnostic			= pPlayer.isAgnostic()
		bBarbarian			= pPlayer.isBarbarian()

		iNumCities			= pPlayer.getNumCities()
		iCulture			= pCity.getCulture(iOwner)
		iNumUnits			= pPlot.getNumUnits()
		iPop				= pCity.getPopulation()

		Manager				= CvEventInterface.getEventManager()
		Civ					= Manager.Civilizations
		Rel					= Manager.Religions
		Tech				= Manager.Techs
		Civic				= Manager.Civics
		Unit				= Manager.Units
		UnitClass			= Manager.UnitClasses
		Mana				= Manager.Mana
		Trait				= Manager.Traits
		Alignment			= Manager.Alignments
		Terrain				= Manager.Terrain
		Feature				= Manager.Feature
		Bonus				= Manager.Resources
		Building			= Manager.Buildings
		BuildingClass		= Manager.BuildingClasses

		if eCiv == Civ["Luchuirp"]:
			if pPlayer.getUnitClassCount(UnitClass["Worker"]) == 0:
				if pCity.canTrain(Unit["Luchuirp"]["Mud Golem"],False,False):
					if getBaseYieldRate(1) >= 3:
						pushOrder(eTrain, Unit["Luchuirp"]["Mud Golem"], -1, False, False, False, True)
						return True
		if hasTech(Tech["Mysticism"]):
			if iNumUnits >= 3:
				iBuilding = civB(BuildingClass["Elder Council"])
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if canConstruct(iBuilding,False,False,False):
						pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
						return True
						
		if hasTech(Tech["Festivals"]):
			if iNumUnits >= 2 and iNumCities >= 4:
				iBuilding = civB(BuildingClass["Market"])
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if canConstruct(iBuilding,False,False,False):
						pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
						return True

		if hasTech(Tech["Smelting"]):
			if iNumUnits >= 2 and iPop >=6:
				if iProductionRank <= 2:
					if iNumCities >= 5:
						iBuilding = civB(BuildingClass["Forge"])
						if iBuilding!=-1 and getNumB(iBuilding) == 0:
							if canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		if hasTech(Tech["Bronze Working"]):
			if eCiv != Civ["Sheaim"]:
				if getBaseYieldRate(1) >=7:
					if iNumUnits >= 4 and iNumCities >= 2:
						iBuilding = civB(BuildingClass["Barracks"])
						if iBuilding!=-1 and getNumB(iBuilding) == 0:
							if canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		if hasTech(Tech["Hunting"]):
			if getBaseYieldRate(1) >=7:
				if iNumUnits >= 4:
					if iNumCities >= 2:
						iBuilding = civB(BuildingClass["Hunting Lodge"])
						if iBuilding!=-1 and getNumB(iBuilding) == 0:
							if canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		if hasTech(Tech["Archery"]):
			if getBaseYieldRate(1) >=7:
				if iNumUnits >= 4:
					if iNumCities >= 2:
						iBuilding = civB(BuildingClass["Fletcher"])
						if iBuilding!=-1 and canConstruct(iBuilding,False,False,False):
							if getNumB(iBuilding) == 0:
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		if eCiv == Civ["Calabim"]:
			if hasTech(Tech["Code of Laws"]):
				iBuilding = Building["Manor"]
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if hasTrait(Trait["Organized"]) or getBaseYieldRate(1) >=6:
						if iNumUnits >= 2:
							if canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		elif eCiv == Civ["Clan of Embers"]:
			if hasTech(Tech["Masonry"]):
				iBuilding = Building["Warrens"]
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if getBaseYieldRate(1) >=7:
						if iNumUnits >= 2:
							if canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		elif eCiv == Civ["Svartalfar"]:
			if hasTech(Tech["Tracking"]):
				if getNumB(Building["Hunting Lodge"]) == 1:
					iBuilding = Building["Shrouded Woods"]
					if iBuilding!=-1 and getNumB(iBuilding) == 0:
						if getBaseYieldRate(1) >=7 and iNumUnits >= 2:
							if canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		elif eCiv == Civ["Luchuirp"]:
			if hasTech(Tech["Sorcery"]):
				if getNumB(Building["Sculptors Studio"]) == 1:
					iBuilding = Building["Blasting Workshop"]
					if iBuilding!=-1 and getNumB(iBuilding) == 0:
						if getBaseYieldRate(1) >=7 and iNumUnits >= 2:
							if canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								return True

		#public baths are insanely good, should be built asap
		if hasTech(Tech["Sanitation"]) and not bBarbarian:
			print ("pb check1")
			if not eCiv == Civ["Infernal"]:
				iBuilding	= Building["Public Baths"]
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if pCity.happyLevel() - pCity.unhappyLevel(1) <0:
						if getBaseYieldRate(1) >=5:
							if iNumUnits >= 2:
								if canConstruct(iBuilding,False,False,False):
									pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
									print ("Pbath built")
									return True

		if hasTech(Tech["Construction"] and not bBarbarian):
			if not eCiv == Civ["Ljosalfar"]:
				if not eCiv == Civ["Svartalfar"]:
					iBuilding = Building["Siege Workshop"]
					if iBuilding!=-1 and getNumB(iBuilding) == 0:
						if iNumCities >= 2 and iNumUnits >= 2:
							if getBCCPM(BuildingClass["Siege Workshop"]) * 3 < iNumCities:
								if getBaseYieldRate(1) >=7:
									if canConstruct(iBuilding,False,False,False):
										pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
										return True

		if eCiv == Civ["Ljosalfar"]:
			if hasTech(Tech["Archery"]):
				iBuilding	= Building["Archery Range"]
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if getBaseYieldRate(1) >=10:
						if iCulture>0:
							if iNumUnits >= 2:
								if canConstruct(iBuilding,False,False,False):
									pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
									print ("Archery Range built")
									return True

		elif eCiv == Civ["Hippus"]:
			if hasTech(Tech["Horseback Riding"]):
				iBuilding	= Building["Stable"]
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if getBaseYieldRate(1) >=10:
						if iCulture>0:
							if iNumUnits >= 2:
								if canConstruct(iBuilding,False,False,False):
									pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
									print ("Stable built")
									return True

		#At peace? Boost science if possible.
		if iWarCount == 0:
			if hasTech(Tech["Writing"]):
				if eCiv != Civ["Clan of Embers"]:
					if eCiv != Civ["Doviello"]:
						if iNumUnits >= 2 and iNumCities >= 3:
							if pCity.getBaseCommerceRate(1) >=10:
								iBuilding = Building["Library"]
								if iBuilding!=-1 and getNumB(iBuilding) == 0:
									if canConstruct(iBuilding,False,False,False):
										pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
										print ("Library built")
										return True

			if hasTech(Tech["Sorcery"]):
				if eCiv != Civ["Svartalfar"]:
					if iNumUnits >= 2:
						if iNumCities >= 5:
							if pCity.getBaseCommerceRate(1) >=20:
								iBuilding	= Building["Alchemy Lab"]
								if iBuilding!=-1 and getNumB(iBuilding) == 0:
									if canConstruct(iBuilding,False,False,False):
										pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
										print ("Alchemy lab built")
										return True

			if hasTech(Tech["Currency"]):
				if not bBarbarian:
					if iNumUnits >= 2:
						if iNumCities >= 5:
							if pCity.getBaseCommerceRate(0) >=20:
								iBuilding	= Building["Moneychanger"]
								if iBuilding!=-1 and getNumB(iBuilding) == 0:
									if canConstruct(iBuilding,False,False,False):
										pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
										print ("Alchemy lab built")
										return True

			#At peace? Reduce maintenance if possible.
			if hasTech(Tech["Code of Laws"]):
				if eCiv != Civ["Calabim"]:
					if iNumUnits >= 2 and iNumCities >= 3:
						if pCity.getMaintenance() >=5:
							iBuilding = civB(BuildingClass["Courthouse"])
							if iBuilding!=-1 and getNumB(iBuilding) == 0:
								if canConstruct(iBuilding,False,False,False):
									pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
									print ("Courthouse built")
									return True

			#Build sewer?.
			if hasTech(Tech["Sanitation"]):
				if eCiv != Civ["Infernal"]:
					if iNumUnits >= 2 and iPop >=6:
						if pCity.getBuildingBadHealth() >=2:
							iBuilding = Building["Sewer"]
							if iBuilding!=-1 and getNumB(iBuilding) == 0:
								if canConstruct(iBuilding,False,False,False):
									pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
									print ("Sewer built")
									return True

			#fix for the -300 AIvalue weight modifier. built smoke and gran if lots of growth potential or health needed
			if hasTech(Tech["Animal Husbandry"]) and not bBarbarian and eCiv != Civ["Infernal"]:
				print ("smokehouse check1")
				iBuilding	= Building["Smokehouse"]
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if iCulture>0:
						if pCity.happyLevel() - pCity.unhappyLevel(1) >7:
							if pCity.foodDifference(False) >=4:
								if getBaseYieldRate(1) >=7:
									if iNumUnits >= 2:
										if canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("Smokehouse built")
											return True
						elif pCity.goodHealth() <= pCity.badHealth(False):
							if pCity.happyLevel() - pCity.unhappyLevel(1) >0:
								if pPlayer.getNumAvailableBonuses(Bonus["Cow"])>0 or pPlayer.getNumAvailableBonuses(Bonus["Pig"])>0 or pPlayer.getNumAvailableBonuses(Bonus["Sheep"])>0:
									if getBaseYieldRate(1) >=5:
										if iNumUnits >= 2:
											if canConstruct(iBuilding,False,False,False):
												pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
												print ("Smokehouse built")
												return True
			if hasTech(Tech["Agriculture"]) and not bBarbarian and eCiv != Civ["Infernal"]:
				print ("granary check1")
				iBuilding = Building["Granary"]
				if iBuilding!=-1 and getNumB(iBuilding) == 0:
					if iCulture>0:
						if pCity.happyLevel() - pCity.unhappyLevel(1) >7:
							if pCity.foodDifference(False) >=4:
								if getBaseYieldRate(1) >=7:
									if iNumUnits >= 2:
										if canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("Granary built")
											return True
						elif pCity.goodHealth() <= pCity.badHealth(False):
							if pCity.happyLevel() - pCity.unhappyLevel(1) >0:
								if pPlayer.getNumAvailableBonuses(Bonus["Wheat"])>0 or pPlayer.getNumAvailableBonuses(Bonus["Corn"])>0 or pPlayer.getNumAvailableBonuses(Bonus["Rice"])>0:
									if getBaseYieldRate(1) >=5:
										if iNumUnits >= 2:
											if canConstruct(iBuilding,False,False,False):
												pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
												print ("Granary built")
												return True

		#spread leaves if elven or has holy city
		if hasTech(Tech["Way of the Forests"]) and not bBarbarian and not bAgnostic:
			print ("leaves temple check1")
			if eCiv == Civ["Ljosalfar"] or eCiv == Civ["Svartalfar"] or isHolyCity(Rel["Fellowship"]):
				if not eRel == Rel["Fellowship"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						iBuilding	= Building["Temple of the Leaves"]
						if iBuilding!=-1 and getNumB(iBuilding) == 0:
							if getBaseYieldRate(1) >=5:
								if iNumUnits >= 2:
									if canConstruct(iBuilding,False,False,False):
										pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
										print ("leaves temple built")
										return True
			print ("leaves disciple check1")
			if eCiv == Civ["Ljosalfar"] or eCiv == Civ["Svartalfar"] or isHolyCity(Rel["Fellowship"]):
				if not eRel == Rel["Fellowship"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel) == True :
					if eRel != -1 and not hasHolyCity(eRel):
						if getNumB(Building["Temple of the Leaves"]) == 1:
							if getUCCPM(UnitClass["Disciple Leaves"]) <=3:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if pCity.canTrain(Unit["Leaves"]["Disciple"],False,False):
											pushOrder(eTrain, Unit["Leaves"]["Disciple"], -1, False, False, False, False)
											print ("leaves disciple built")
											return True
		#spread runes if dwarven or has holy city
		if hasTech(Tech["Way of the Earthmother"]) and not bBarbarian and not bAgnostic:
			print ("runes temple check1")
			if eCiv == Civ["Khazad"] or eCiv == Civ["Luchuirp"] or isHolyCity(Rel["Runes of Kilmorph"]):
				if not eRel == Rel["Runes of Kilmorph"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel) == True :
					if eRel != -1 and not hasHolyCity(eRel):
						iBuilding	= Building["Temple of the Kilmorph"]
						if iBuilding!=-1 and getNumB(iBuilding) == 0:
							if getBaseYieldRate(1) >=5:
								if iNumUnits >= 2:
									if canConstruct(iBuilding,False,False,False):
										pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
										print ("runes temple built")
										return True
			print ("runes disciple check1")
			if eCiv == Civ["Khazad"] or eCiv == Civ["Luchuirp"] or isHolyCity(Rel["Runes of Kilmorph"]):
				if not eRel == Rel["Runes of Kilmorph"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if getNumB(Building["Temple of the Kilmorph"]) == 1:
							if getUCCPM(UnitClass["Disciple Kilmorph"]) <=3:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if pCity.canTrain(Unit["Runes"]["Disciple"],False,False):
											pushOrder(eTrain, Unit["Runes"]["Disciple"], -1, False, False, False, False)
											print ("runes disciple built")
											return True
		#spread esus if has holy city, spreading it is cheap, but don't produce nightwatches all day long
		if hasTech(Tech["Deception"]) and not bBarbarian and not bAgnostic:
			print ("esus disc check1")
			if isHolyCity(Rel["Council of Esus"]):
				if randNum(100, "Esusspread") <= 20:
					if not eRel == Rel["Council of Esus"]:
						if getBaseYieldRate(1) >=5:
							if iNumUnits >= 2:
								if pCity.canTrain(Unit["Esus"]["Nightwatch"],False,False):
									pushOrder(eTrain, Unit["Esus"]["Nightwatch"], -1, False, False, False, False)
									print ("nightwatch built")
									return True
		#spread the empyrean if has holy city
		if hasTech(Tech["Honor"]) and not bBarbarian and not bAgnostic:
			print ("empy temple check1")
			if isHolyCity(Rel["Empyrean"]):
				if not eRel == Rel["Empyrean"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Evil"]:
							iBuilding	= Building["Temple of the Empyrean"]
							if getNumB(Building["Temple of the Empyrean"]) == 0:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("empyrean temple built")
											return True
			print ("empy disc check1")
			if isHolyCity(Rel["Empyrean"]):
				if not eRel == Rel["Empyrean"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Evil"]:
							if getNumB(Building["Temple of the Empyrean"]) == 1:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if pCity.canTrain(Unit["Empyrean"]["Disciple"],False,False):
											pushOrder(eTrain, Unit["Empyrean"]["Disciple"], -1, False, False, False, False)
											print ("empyrean disciple built")
											return True
		#spread the order if has holy city
		if hasTech(Tech["Orders from Heaven"]) and not bBarbarian and not bAgnostic:
			print ("order temple check1")
			if isHolyCity(Rel["Order"]):
				if not eRel == Rel["Order"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Evil"]:
							iBuilding	= Building["Temple of the Order"]
							if iBuilding!=-1 and getNumB(iBuilding) == 0:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("order temple built")
											return True
			print ("order aco check1")
			if isHolyCity(Rel["Order"]):
				if not eRel == Rel["Order"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Evil"]:
							if getNumB(Building["Temple of the Order"]) == 1:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if pCity.canTrain(Unit["Order"]["Disciple"],False,False):
											pushOrder(eTrain, Unit["Order"]["Disciple"], -1, False, False, False, False)
											print ("order disciple built")
											return True
		#spread the veil if has holy city
		if hasTech(Tech["Corruption of Spirit"]) and not bBarbarian and not bAgnostic:
			print ("Veil1 check")
			if isHolyCity(Rel["Ashen Veil"]):
				if not eRel == Rel["Ashen Veil"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Good"]:
							iBuilding	= Building["Temple of the Veil"]
							if iBuilding!=-1 and getNumB(iBuilding) == 0:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("veil temple built")
											return True
			print ("veil disc check1")
			if isHolyCity(Rel["Ashen Veil"]):
				if not eRel == Rel["Ashen Veil"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Good"]:
							if getNumB(Building["Temple of the Veil"]) == 1:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if pCity.canTrain(Unit["Veil"]["Disciple"],False,False):
											pushOrder(eTrain, Unit["Veil"]["Disciple"], -1, False, False, False, False)
											bOverride = True
											print ("veil disciple built")
											return True
		#spread the overlords if has holy city
		if hasTech(Tech["Message from the Deep"]) and not bBarbarian and not bAgnostic:
			print ("Octo1 check")
			if isHolyCity(Rel["Octopus Overlords"]):
				if not eRel == Rel["Octopus Overlords"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Good"]:
							iBuilding	= Building["Temple of the Overlords"]
							if iBuilding!=-1 and getNumB(iBuilding) == 0:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("octo temple built")
											return True

			print ("Octo disc check1")
			if isHolyCity(Rel["Octopus Overlords"]):
				if not eRel == Rel["Octopus Overlords"]:
#Snarko 25/05/2010
#eRel can be NO_RELIGION!
##orig					if not hasHolyCity(eRel):
					if eRel != -1 and not hasHolyCity(eRel):
						if not eAlignment == Alignment["Good"]:
							if getNumB(Building["Temple of the Overlords"]) == 1:
								if getBaseYieldRate(1) >=5:
									if iNumUnits >= 2:
										if pCity.canTrain(Unit["Overlords"]["Disciple"],False,False):
											pushOrder(eTrain, Unit["Overlords"]["Disciple"], -1, False, False, False, False)
											print ("octo disciple built")
											return True
		#build the towers if possible
		if hasTech(Tech["Elementalism"]) and not bBarbarian:
			print ("ele tower check1")
			if getBCCPM(BuildingClass["Tower of Elements"]) == 0:
				if hasBonus(Mana["Fire"]):
					if hasBonus(Mana["Water"]):
						if hasBonus(Mana["Air"]):
							if hasBonus(Mana["Earth"]):
								if getBaseYieldRate(1) >=25:
									if iNumUnits >= 2:
										iBuilding	= Building["Tower of Elements"]
										if iBuilding!=-1 and canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("element tower built")
											return True
		if hasTech(Tech["Divination"]) and not bBarbarian:
			print ("div tower check1")
			if getBCCPM(BuildingClass["Tower of Divination"]) == 0:
				if hasBonus(Mana["Sun"]):
					if hasBonus(Mana["Spirit"]):
						if hasBonus(Mana["Law"]):
							if hasBonus(Mana["Mind"]):
								if getBaseYieldRate(1) >=25:
									if iNumUnits >= 2:
										iBuilding	= Building["Tower of Divination"]
										if iBuilding!=-1 and canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("div tower built")
											return True
		if hasTech(Tech["Necromancy"]) and not bBarbarian:
			print ("tower necro check1")
			if getBCCPM(BuildingClass["Tower of Necromancy"]) == 0:
				if (hasBonus(Mana["Shadow"]) and hasBonus(Mana["Death"]) and hasBonus(Mana["Entropy"]) and hasBonus(Mana["Chaos"])):
					if getBaseYieldRate(1) >=25:
						if iNumUnits >= 2:
							iBuilding	= Building["Tower of Necromancy"]
							if iBuilding!=-1 and canConstruct(iBuilding,False,False,False):
								pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
								print ("necro tower built")
								return True
		if hasTech(Tech["Alteration"]) and not bBarbarian:
			print ("tower alt check1")
			if getBCCPM(BuildingClass["Tower of Alteration"]) == 0:
				if hasBonus(Mana["Body"]):
					if hasBonus(Mana["Nature"]):
						if hasBonus(Mana["Life"]):
							if hasBonus(Mana["Enchantment"]):
								if getBaseYieldRate(1) >=25:
									if iNumUnits >= 2:
										iBuilding	= Building["Tower of Alteration"]
										if iBuilding!=-1 and canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("alteration tower built")
											return True

		#prioritize the nat epic
		if hasTech(Tech["Warfare"]) and hasTech(Tech["Writing"]) and not bBarbarian:
			print ("lib epic check1")
			if getBCCPM(BuildingClass["National Epic"]) == 0:
				iBuilding = civB(BuildingClass["Library"])
				if getNumB(iBuilding) == 0:
					if pCity.getBaseGreatPeopleRate() >=12:
						if getBaseYieldRate(1) >=10:
							if iNumUnits >= 2:
								if not eCiv == Civ["Clan of Embers"]:
									if not eCiv == Civ["Doviello"]:
										if iBuilding!=-1 and canConstruct(iBuilding,False,False,False):
											pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
											print ("nat epic library built")
											return True
			print ("nat epic check1")
			if getBCCPM(BuildingClass["National Epic"]) == 0:
				iBuilding = civB(BuildingClass["Library"])
				if getNumB(iBuilding) == 1:
					if pCity.getBaseGreatPeopleRate() >=12:
						if getBaseYieldRate(1) >=10:
							if iNumUnits >= 2:
								iBuilding = Building["National Epic"]
								if iBuilding!=-1 and canConstruct(iBuilding,False,False,False):
									pushOrder(eConstruct, iBuilding, -1, False, False, False, False)
									print ("nat epic built")
									return True
		#prioritize the heroic epic
		if hasTech(Tech["Warfare"]) and not bBarbarian:
			print ("heroic epic check1")
			if getBCCPM(BuildingClass["Heroic Epic"]) == 0:
				if iProductionRank == 1:
					iBuilding	= Building["Heroic Epic"]
					bHeroic 	= canConstruct(iBuilding,False,False,False)
					if bHeroic:
						if getBaseYieldRate(1) >=10:
							if iNumUnits >= 2:
								pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
								print ("heroic epic built")
								return True
		#build the shrine in the he city
		if not bBarbarian:
			print ("championshrine check1")
			if getBCCPM(BuildingClass["Shrine of Champion"]) == 0:
				if getNumB(BuildingClass["Heroic Epic"]) == 1:
					if iNumUnits >= 2:
						if canConstruct(Building["Shrine of the Champion"],False,False,False):
							pushOrder(eConstruct, Building["Shrine of the Champion"], -1, False, False, False, True)
							print ("Shrine of the Champion built")
							return True
		#Civ can build a Hero?
		if iProductionRank <= 2:
			print ("Rank Hero Check1")
			if getBaseYieldRate(1) >= 10:
				# Might need to rewrite this...
				print ("Rank Hero Check2")
				sHero=['UNITCLASS_DONAL','UNITCLASS_TEUTORIX','UNITCLASS_CORLINDALE','UNITCLASS_BASIUM','UNITCLASS_GUYBRUSH']
				sHero=sHero+['UNITCLASS_EURABATRES','UNITCLASS_GILDEN','UNITCLASS_MAROS','UNITCLASS_MAGNADINE']
				sHero=sHero+['UNITCLASS_GOVANNON','UNITCLASS_LOKI','UNITCLASS_RANTINE','UNITCLASS_ALAZKAN']
				sHero=sHero+['UNITCLASS_LOSHA','UNITCLASS_ABASHI','UNITCLASS_RATHUS','UNITCLASS_WILBOMAN','UNITCLASS_HYBOREM']
				sHero=sHero+['UNITCLASS_YVAIN','UNITCLASS_KITHRA','UNITCLASS_BAMBUR','UNITCLASS_ARTHENDAIN']
				sHero=sHero+['UNITCLASS_SAVEROUS','UNITCLASS_HEMAH','UNITCLASS_ROSIER','UNITCLASS_MARDERO']
				sHero=sHero+['UNITCLASS_VALIN','UNITCLASS_SPHENER','UNITCLASS_CHALID','UNITCLASS_GIBBON','UNITCLASS_DUIN']
				for k in range(len(sHero)):
					iUnit = infoCiv.getCivilizationUnits(getInfoType(sHero[k]))
					if iUnit != -1:
						if pCity.canTrain(iUnit,False,False):
							print iUnit
							pushOrder(eTrain,iUnit,-1, False, False, False, True)
							print ("Hero %s built"%(gc.getUnitInfo(iUnit).getType()))
							return True
		# helping the Illians understand their temple
		if eCiv == Civ["Illians"]:
			if getNumB(Building["Temple of the Hand"]) == 0:
				print ("Illian snowtemple check")
				iTaigacounter = 0
				getPlot = pCity.getCityIndexPlot
				for iI in xrange(1, 21):
					pLoopPlot = getPlot(iI)
					if pLoopPlot:
						print iTaigacounter
						if not pLoopPlot.isNone():
							if not pLoopPlot.isWater():
								eTerrain = pLoopPlot.getTerrainType()
								if   eTerrain == Terrain["Taiga"]: 		iTaigacounter += 1
								elif eTerrain == Terrain["Desert"]: 		iTaigacounter += 1
								eFeature = pLoopPlot.getFeatureType()
								if   eFeature == Feature["Jungle"]:			iTaigacounter += 1
								elif eFeature == Feature["Flood Plains"]:	iTaigacounter -= 3
								elif eFeature == Feature["Scrub"]: 			iTaigacounter += 1
								if pLoopPlot.isRiverSide(): iTaigacounter -= 1
				if iTaigacounter >= 1:
					if iNumUnits >= 2:
						if canConstruct(Building["Temple of the Hand"],False,False,False):
							pushOrder(eConstruct, Building["Temple of the Hand"], -1, False, False, False, False)
							print ("Ice Temple built")
							return True
		#get one military building in each city. some weighting for diversity

				'''
		if hasTech(Tech["Bronze Working"]) or hasTech(Tech["Archery"]) or hasTech(Tech["Hunting"]) or hasTech(Tech["Horseback Riding"]):
			iBuilding1 = civB(BuildingClass["Barracks"])
			iBuilding2 = civB(BuildingClass["Fletcher"])
			iBuilding3 = civB(BuildingClass["Hunting Lodge"])
			iBuilding4 = civB(BuildingClass["Stable"])
			iCount=0
			if getNumB(iBuilding1) ==1: iCount +=1
			if getNumB(iBuilding2) ==1: iCount +=1
			if getNumB(iBuilding3) ==1: iCount +=1
			if getNumB(iBuilding4) ==1: iCount +=1
			if iCount == 0:
				iBarracks = 0; 		iFletcher = 0
				iHuntingLodge = 0; 	iStable = 0
				if hasTech(Tech["Bronze Working"]):
					iBarracks += 1000
					iBarracks += getBCCPM(iBuilding2)*50
					iBarracks += getBCCPM(iBuilding3)*50
					iBarracks += getBCCPM(iBuilding4)*50
					if hasTech(Tech["Iron Working"]): 	iBarracks += 1000
					if hasBonus(Bonus["Mithril"]): 		iBarracks += 600
					elif hasBonus(Bonus["Iron"]):		iBarracks += 400
					elif hasBonus(Bonus["Copper"]):		iBarracks += 200
					if hasBonus(Mana["Enchantment"]):
						if hasTech(Tech["Knowledge of the Ether"]):	iBarracks += 200
					if eCiv == Civ["Khazad"]:	iBarracks += 2000
					if isCivic(Civic["Nationhood"]):	iBarracks += 200
				if hasTech(Tech["Archery"]):
					iFletcher += 1000
					iFletcher += getBCCPM(iBuilding1)*50
					iFletcher += getBCCPM(iBuilding3)*50
					iFletcher += getBCCPM(iBuilding4)*50
					if hasTech(Tech["Bowyers"]): 	 iFletcher += 1000
					if hasTrait(Trait["Defender"]):  iFletcher += 400
					if hasTrait(Trait["Dexterous"]): iFletcher += 200
					if hasBonus(Mana["Enchantment"]):
						if hasTech(Tech["Sorcery"]): iFletcher += 400
				if hasTech(Tech["Hunting"]):
					iHuntingLodge += 1000
					iHuntingLodge += getBCCPM(iBuilding1)*50
					iHuntingLodge += getBCCPM(iBuilding2)*50
					iHuntingLodge += getBCCPM(iBuilding4)*50
					if hasTech(Tech["Animal Handling"]): iHuntingLodge += 1000
					if hasTech(Tech["Poisons"]):		 iHuntingLodge += 400
					if hasTrait(Trait["Sinister"]):		 iHuntingLodge += 200
					if hasBonus(Mana["Nature"]):
						if hasTech(Tech["Sorcery"]): 	 iHuntingLodge += 200
				if hasTech(Tech["Horseback Riding"]):
					iStable += 1000
					iStable += getBCCPM(iBuilding1)*50
					iStable += getBCCPM(iBuilding2)*50
					iStable += getBCCPM(iBuilding3)*50
					if hasTech(Tech["Stirrups"]): 		iStable += 1000
					if hasTrait(Trait["Horselord"]): 	iStable += 200
					if hasTrait(Trait["Raiders"]): 		iStable += 200
					if eCiv == Civ["Kuriotates"]:		iStable += 400
				if iCulture>0:
					if getBaseYieldRate(1) >= 8:
						if iNumUnits >= 2:
							if iBarracks>=iStable and iBarracks>=iHuntingLodge and iBarracks>=iFletcher and canConstruct(iBuilding1,False,False,False):
								if canConstruct(iBuilding1,False,False,False):
									pushOrder(eConstruct, iBuilding1, -1, False, False, False, True)
									print ("Barracks built")
									return True
							elif iFletcher>=iBarracks and iFletcher>=iHuntingLodge and iFletcher>=iStable and canConstruct(iBuilding2,False,False,False):
								if canConstruct(iBuilding2,False,False,False):
									pushOrder(eConstruct, iBuilding2, -1, False, False, False, True)
									print ("Fletcher built")
									return True
							elif iHuntingLodge>=iBarracks and iHuntingLodge>=iFletcher and iHuntingLodge>=iStable and canConstruct(iBuilding3,False,False,False):
								if canConstruct(iBuilding3,False,False,False):
									pushOrder(eConstruct, iBuilding3, -1, False, False, False, True)
									print ("Hunting Lodge built")
									return True
							elif iStable>=iBarracks and iStable>=iFletcher and iStable>=iHuntingLodge and canConstruct(iBuilding4,False,False,False):
								if canConstruct(iBuilding4,False,False,False):
									pushOrder(eConstruct, iBuilding4, -1, False, False, False, True)
									print ("Stable built")
									return True
				'''

		#if at war we need some catapults
		if hasTech(Tech["Construction"]) and not bBarbarian:
			print ("cata check1")
			if not hasTech(Tech["Blasting Powder"]) and iWarCount > 0:
				print ("warplan check1")
				if eCiv not in (Civ["Ljosalfar"],Civ["Svartalfar"],Civ["Khazad"],Civ["Luchuirp"]):
					if getNumB(Building["Siege Workshop"]) == 1:
						if iNumCities > 5 * getUCCPM(UnitClass["Catapult"]):
							if getBaseYieldRate(1) >=7:
								if iNumUnits >= 2:
									iUnit	= Unit["Generic"]["Catapult"]
									if pCity.canTrain(iUnit,False,False):
										pushOrder(eTrain, iUnit, -1, False, False, False, False)
										print ("Catapult built")
										return True

		#Only One City?
		if hasTech(Tech["Bronze Working"]) or hasTech(Tech["Archery"]):
			if eCiv not in (Civ["Khazad"], Civ["Kuriotates"]):
				if not getUCCPM(UnitClass["Settler"]) >= 1 and iNumCities < 2:
					print ("settler check1")
					if iWarCount == 0:
						iBuildSettler = 0
						if hasTech(Tech["Ancient Chants"]):	iBuildSettler += 2
						if iPop >=6:						iBuildSettler += 2
						if hasTrait(Trait["Expansive"]):	iBuildSettler += 2
						if hasTrait(Trait["Creative"]):		iBuildSettler += 2
						if getNumB(Building["Market"]) == 1:iBuildSettler += 2
						if iNumUnits >= 8:					iBuildSettler += 2
						if iGold / iNumCities >= 149:		iBuildSettler += 2
						if isCivic(Civic["City States"]):	iBuildSettler *= 2
						if isCivic(Civic["God King"]):		iBuildSettler -= 2
						if iBuildSettler >= 5:
							if getBaseYieldRate(1) >=7:
								if iNumUnits >= 5:
									if pCity.canTrain(Unit["Generic"]["Settler"],False,False):
										pushOrder(eTrain, Unit["Generic"]["Settler"], -1, False, False, False, False)
										print ("First Settler Built")
										return True

		#do we need to expand?
		if hasTech(Tech["Festivals"]) or hasTech(Tech["Code of Laws"]):
			print ("settler check2")
			if iWarCount == 0 and iNumCities < 5:
				iBuildSettler = 0
				if hasTrait(Trait["Expansive"]):		iBuildSettler += 2
				if hasTrait(Trait["Creative"]):			iBuildSettler += 1
				if iNumCities <= 3:						iBuildSettler += 2
				if getNumB(Building["Market"]) == 1:	iBuildSettler += 1
				if getNumB(Building["Courthouse"]) == 1:iBuildSettler += 1
				if iGold / iNumCities >= 149:			iBuildSettler += 1
				if iGold / iNumCities <= 25:			iBuildSettler -= 1
				if isCivic(Civic["City States"]):		iBuildSettler *= 2
				if isCivic(Civic["God King"]):			iBuildSettler -= 2
				if iBuildSettler > 3:
					if not eCiv == Civ["Khazad"]:
						if getUCCPM(UnitClass["Settler"]) < 1:
							if getBaseYieldRate(1) >=7:
								if iNumUnits >= 3:
									if pCity.canTrain(Unit["Generic"]["Settler"],False,False):
										pushOrder(eTrain, Unit["Generic"]["Settler"], -1, False, False, False, False)
										print ("Settler Built")
										return True

				'''
		if iPop >= 3:
			getProdTime 		= pCity.getBuildingProductionTime
			getNumRealBuilding 	= pCity.getNumRealBuilding

			iBuilding 		= civB(BuildingClass["Fletcher"])
			if (iBuilding != -1):
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			iBuilding = civB(BuildingClass["Barracks"])
			if (iBuilding != -1):
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			iBuilding = civB(BuildingClass["Archery Range"])
			if (iBuilding != -1):
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			iBuilding = civB(BuildingClass["Hunting Lodge"])
			if (iBuilding != -1):
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			iBuilding = civB(BuildingClass["Courthouse"])
			if (iBuilding != -1):
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			iBuilding = civB(BuildingClass["Market"])
			if (iBuilding != -1):
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			iBuilding = civB(BuildingClass["Siege Workshop"])
			if not eCiv == Civ["Svartalfar"] and not eCiv == Civ["Ljosalfar"]:
				if (iBuilding != -1):
					if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
						pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
						return True

			if eCiv == Civ["Lanun"]:
				iBuilding = Building["Harbor Lanun"]
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

				iBuilding = Building["Lighthouse"]
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			elif eCiv == Civ["Amurites"]:
				iBuilding = Building["Wizards Hall"]
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

				iBuilding = Building["Meditation Hall"]
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

				iBuilding = Building["Vault Gate"]
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			elif eCiv == Civ["Sheaim"]:
				iBuilding = Building["Planar Gate"]
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

				iBuilding = Building["Mage Guild"]
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True

			elif eCiv == Civ["Hippus"]:
				iBuilding = civB(BuildingClass["Stable"])
				if getNumRealBuilding(iBuilding) == 0 and canConstruct(iBuilding, False, False, False) and getProdTime(iBuilding) < scale(15):
					pushOrder(eConstruct, iBuilding, -1, False, False, False, True)
					return True
				'''

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['AI_chooseProduction']:
			if module.AI_chooseProduction(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def AI_unitUpdate(self,argsList):
		pUnit 		= argsList[0]
		iOwner		= pUnit.getOwner()
		gc			= CyGlobalContext()
		getInfoType	= gc.getInfoTypeForString
		pPlot 		= pUnit.plot()
		eUnitType	= pUnit.getUnitType()
		eUnitClass	= pUnit.getUnitClassType()

		Manager		= CvEventInterface.getEventManager()
		UnitClass	= Manager.UnitClasses
		Unit		= Manager.Units
		Hero		= Manager.Heroes
		Lair		= Manager.Lairs
		Improvement	= Manager.Improvements
		UnitType	= pUnit.getUnitType()
		iNumUnits	= pPlot.getNumUnits()
		bAnimal		= pUnit.isAnimal()

		if eUnitClass == UnitClass["Giant Spider"]:
			iX = pUnit.getX(); iY = pUnit.getY()
			if pPlot.isOwned():	return 0
			getPlot = CyMap().plot
			for iiX,iiY in RANGE1:
				pLoopPlot = getPlot(iX+iiX,iY+iiY)
				for i in xrange(pLoopPlot.getNumUnits()):
					if pLoopPlot.getUnit(i).getOwner() != iOwner:
						return 0
			return 1

		if eUnitType == Hero["Acheron"]:
			if pPlot.isVisibleEnemyUnit(iOwner):
				pUnit.cast(getInfoType('SPELL_BREATH_FIRE'))

		if not isLimitedUnitClass(eUnitClass):
			iImprovement = pPlot.getImprovementType()
			if iImprovement != -1:
				if (iImprovement == Lair["Barrow"] or iImprovement == Lair["Ruins"] or iImprovement == Improvement["Hellfire"]):
					if pUnit.getDamage() == 0:
						if not bAnimal:
							if iNumUnits - pPlot.getNumAnimalUnits() == 1:
								return 1
				if (iImprovement == Lair["Bear Den"] or iImprovement == Lair["Lion Den"]):
					if pUnit.getDamage() == 0:
						if bAnimal:
							if pPlot.getNumAnimalUnits() == 1:
								return 1
				if iImprovement == Lair["Goblin Camp"]:
					if pUnit.getDamage() == 0:
						if not bAnimal:
							if iNumUnits - pPlot.getNumAnimalUnits() <= 3:
								return 1

		iImprovement = pPlot.getImprovementType()
		if iImprovement != -1:
			if (iImprovement == Lair["Barrow"] or iImprovement == Lair["Ruins"] or iImprovement == Improvement["Hellfire"]):
				if not bAnimal:
					if iNumUnits - pPlot.getNumAnimalUnits() == 1:
						return 1
			if (iImprovement == Lair["Bear Den"] or iImprovement == Lair["Lion Den"]):
				if bAnimal:
					if pPlot.getNumAnimalUnits() == 1:
						return 1
			if iImprovement == Lair["Goblin Camp"]:
				if not bAnimal:
					if iNumUnits - pPlot.getNumAnimalUnits() <= 3:
						return 1

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['AI_unitUpdate']:
			if module.AI_unitUpdate(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def AI_doWar(self,argsList):
		pTeam = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['AI_doWar']:
			if module.AI_doWar(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def AI_doDiplo(self,argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['AI_doDiplo']:
			if module.AI_doDiplo(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def calculateScore(self,argsList):
		ePlayer 	= argsList[0]
		bFinal 		= argsList[1]
		bVictory 	= argsList[2]
		gc 			= CyGlobalContext()
		scoreComp 	= CvUtil.getScoreComponent
		pPlayer 	= gc.getPlayer(ePlayer)
		game		= CyGame()
		getDefINT	= gc.getDefineINT

		iPopulationScore 	= scoreComp(pPlayer.getPopScore(), game.getInitPopulation(), game.getMaxPopulation(), getDefINT("SCORE_POPULATION_FACTOR"), True, bFinal, bVictory)
		iLandScore 			= scoreComp(pPlayer.getLandScore(), game.getInitLand(), game.getMaxLand(), getDefINT("SCORE_LAND_FACTOR"), True, bFinal, bVictory)
		iTechScore 			= scoreComp(pPlayer.getTechScore(), game.getInitTech(), game.getMaxTech(), getDefINT("SCORE_TECH_FACTOR"), True, bFinal, bVictory)
		iWondersScore 		= scoreComp(pPlayer.getWondersScore(), game.getInitWonders(), game.getMaxWonders(), getDefINT("SCORE_WONDER_FACTOR"), False, bFinal, bVictory)

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		modularScore = 0
		for module in command['calculateScore']:
			modularScore += module.calculateScore(self, argsList)

		## Modular Python End
		## *******************

		return int(iPopulationScore + iLandScore + iWondersScore + iTechScore + modularScore)

	def doHolyCity(self):

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doHolyCity']:
			if module.doHolyCity(self):
				return True

		## Modular Python End
		## *******************

		return False

	def doHolyCityTech(self,argsList):
		pTeam = argsList[0]
		ePlayer = argsList[1]
		eTech = argsList[2]
		bFirst = argsList[3]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doHolyCityTech']:
			if module.doHolyCityTech(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doGold(self,argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doGold']:
			if module.doGold(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doResearch(self,argsList):
		ePlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doResearch']:
			if module.doResearch(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doGoody(self,argsList):
		ePlayer = argsList[0]
		pPlot = argsList[1]
		pUnit = argsList[2]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doGoody']:
			if module.doGoody(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doGrowth(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doGrowth']:
			if module.doGrowth(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotGrow(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotGrow']:
			if module.cannotGrow(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotStarve(self,argsList):
		pCity = argsList[0]
		## modified: estyles 24-Oct-2010

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['cannotStarve']:
			if module.cannotStarve(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotSpreadReligionHere(self,argsList):
		pCity = argsList[0]
		gc 		= CyGlobalContext()

		Manager		= CvEventInterface.getEventManager()
		Civ			= Manager.Civilizations

		pPlayer = gc.getPlayer(pCity.getOwner())

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotSpreadReligionHere']:
			if module.cannotSpreadReligionHere(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doProduction(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doProduction']:
			if module.doProduction(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doCulture(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doCulture']:
			if module.doCulture(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doPlotCulture(self,argsList):
		pCity = argsList[0]
		bUpdate = argsList[1]
		ePlayer = argsList[2]
		iCultureRate = argsList[3]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doPlotCulture']:
			if module.doPlotCulture(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doReligion(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doReligion']:
			if module.doReligion(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def cannotSpreadReligion(self,argsList):
		iOwner, iUnitID, iReligion, iX, iY = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['cannotSpreadReligion']:
			if module.cannotSpreadReligion(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doGreatPeople(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doGreatPeople']:
			if module.doGreatPeople(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doMeltdown(self,argsList):
		pCity = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doMeltdown']:
			if module.doMeltdown(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doReviveActivePlayer(self,argsList):
		"allows you to perform an action after an AIAutoPlay"
		iPlayer = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doReviveActivePlayer']:
			if module.doReviveActivePlayer(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doPillageGold(self, argsList):
		"controls the gold result of pillaging"
		pPlot 			= argsList[0]
		pUnit 			= argsList[1]
		gc 				= CyGlobalContext()
		game			= CyGame()
		eImprovement 	= pPlot.getImprovementType()
		iPillage 		= gc.getImprovementInfo(eImprovement).getPillageGold()
		randNum			= game.getSorenRandNum

		iPillageGold = 0
		iPillageGold = 	randNum(iPillage, "Pillage Gold 1")
		iPillageGold +=	randNum(iPillage, "Pillage Gold 2")

		iPillageGold += (pUnit.getPillageChange() * iPillageGold) / 100

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doPillageGold']:
			iPillageGold += module.doPillageGold(self, argsList)

		## Modular Python End
		## *******************

		return iPillageGold

	def doCityCaptureGold(self, argsList):
		"controls the gold result of capturing a city"
		pOldCity 		= argsList[0]
		gc 		 		= CyGlobalContext()
		randNum			= CyGame().getSorenRandNum
		getDefINT		= gc.getDefineINT
		iCaptureGold 	= 0
		iGameTurn		= CyGame().getGameTurn()

		iCaptureGold += getDefINT("BASE_CAPTURE_GOLD")
		iCaptureGold += (pOldCity.getPopulation() * getDefINT("CAPTURE_GOLD_PER_POPULATION"))
		iCaptureGold += randNum(getDefINT("CAPTURE_GOLD_RAND1"), "Capture Gold 1")
		iCaptureGold += randNum(getDefINT("CAPTURE_GOLD_RAND2"), "Capture Gold 2")

		iGoldMaxTurns = getDefINT("CAPTURE_GOLD_MAX_TURNS")

		if (iGoldMaxTurns > 0):
			iCaptureGold *= cyIntRange((iGameTurn - pOldCity.getGameTurnAcquired()), 0, getDefINT("CAPTURE_GOLD_MAX_TURNS"))
			iCaptureGold /= iGoldMaxTurns

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doCityCaptureGold']:
			iCaptureGold += module.doCityCaptureGold(self, argsList)

		## Modular Python End
		## *******************

		return iCaptureGold

	def citiesDestroyFeatures(self,argsList):
		iX, iY= argsList

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['citiesDestroyFeatures']:
			if not module.citiesDestroyFeatures(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def canFoundCitiesOnWater(self,argsList):
		iX, iY= argsList

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canFoundCitiesOnWater']:
			if module.canFoundCitiesOnWater(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def doCombat(self,argsList):
		pSelectionGroup, pDestPlot = argsList

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['doCombat']:
			if module.doCombat(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False

	def getConscriptUnitType(self, argsList):
		iPlayer = argsList[0]
		iConscriptUnitType = -1 #return this with the value of the UNIT TYPE you want to be conscripted, -1 uses default system

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getConscriptUnitType']:
			modularReturn = module.getConscriptUnitType(self, argsList)
			if modularReturn != -1:
				return modularReturn

		## Modular Python End
		## *******************

		return iConscriptUnitType

	def getCityFoundValue(self, argsList):
		iPlayer, iPlotX, iPlotY = argsList
		iFoundValue = -1 # Any value besides -1 will be used

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getCityFoundValue']:
			modularReturn = module.getCityFoundValue(self, argsList)
			if modularReturn != -1:
				iFoundValue += modularReturn

		## Modular Python End
		## *******************

		return iFoundValue

	def canPickPlot(self, argsList):
		pPlot = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canPickPlot']:
			if not module.canPickPlot(self, argsList):
				return False

		## Modular Python End
		## *******************

		return True

	def getUnitCostMod(self, argsList):
		iPlayer, iUnit = argsList
		iCostMod = -1 # Any value > 0 will be used

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getUnitCostMod']:
			modularReturn = module.getUnitCostMod(self, argsList)
			if modularReturn > 0:
				iCostMod += modularReturn

		## Modular Python End
		## *******************

		return iCostMod

	def getBuildingCostMod(self, argsList):
		iPlayer, iCityID, iBuilding = argsList
		gc 		= CyGlobalContext()
		pPlayer = gc.getPlayer(iPlayer)
		pCity 	= pPlayer.getCity(iCityID)

		iCostMod = -1 # Any value > 0 will be used
		Manager		= CvEventInterface.getEventManager()
		Manager.verifyLoaded()
		Building	= Manager.Buildings

		if iBuilding == Building["Gambling House"]:
			if pPlayer.isGamblingRing():
				#iCostMod = gc.getBuildingInfo(iBuilding).getProductionCost() / 4
				iCostMod = 25
		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getBuildingCostMod']:
			modularReturn = module.getBuildingCostMod(self, argsList)
			if modularReturn > 0:
				iCostMod += modularReturn

		## Modular Python End
		## *******************

		return iCostMod

	def canUpgradeAnywhere(self, argsList):
		pUnit = argsList

		#b should mean boolean, so why is this using an int, and why is it different from every other function in this file?
		#I'm going to change it for consistency - estyles
		#bCanUpgradeAnywhere = 0

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['canUpgradeAnywhere']:
			if module.canUpgradeAnywhere(self, argsList):
				return True

		## Modular Python End
		## *******************

		return False
		#below line removed and replaced with above for consistency
		#return bCanUpgradeAnywhere

	def getWidgetHelp(self, argsList):
		eWidgetType, iData1, iData2, bOption = argsList
		gc = CyGlobalContext()
		# DynTraits Start
		if eWidgetType == WidgetTypes.WIDGET_PYTHON:
			if iData1 == 8001:
				return CyTranslator().getText("TXT_KEY_DYN_TRAITS",())
                # DynTraits End
			if iData1 == 1001: return CyTranslator().getText("TXT_KEY_CONCEPT_BUILDINGS",())
			if iData1 == 1002: return CyTranslator().getText("TXT_KEY_CONCEPT_WONDERS",())
			if iData1 == 1003: return CyTranslator().getText("TXT_KEY_PEDIA_EFFECTS",())
			if iData1 == 1004: return CyTranslator().getText("TXT_KEY_HEADING_TRADEROUTE_LIST",())
			if iData1 == 1005: return CyTranslator().getText("TXT_KEY_TRAINING_LABEL",())

## Religion Screen ##
		if eWidgetType == WidgetTypes.WIDGET_HELP_RELIGION:
			if iData1 == -1:
				return CyTranslator().getText("TXT_KEY_CULTURELEVEL_NONE", ())
## Platy WorldBuilder ##
		elif eWidgetType == WidgetTypes.WIDGET_PYTHON:
			if iData1 == 1027:
				return CyTranslator().getText("TXT_KEY_WB_PLOT_DATA",())
			elif iData1 == 1028:
				return gc.getGameOptionInfo(iData2).getHelp()
			elif iData1 == 1029:
				if iData2 == 0:
					sText = CyTranslator().getText("TXT_KEY_WB_PYTHON", ())
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onFirstContact"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onChangeWar"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onVassalState"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onCityAcquired"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onCityBuilt"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onCultureExpansion"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onGoldenAge"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onEndGoldenAge"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onGreatPersonBorn"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onPlayerChangeStateReligion"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onReligionFounded"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onReligionSpread"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onReligionRemove"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onCorporationFounded"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onCorporationSpread"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onCorporationRemove"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onUnitCreated"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onUnitLost"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onUnitPromoted"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onBuildingBuilt"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onProjectBuilt"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onTechAcquired"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onImprovementBuilt"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onImprovementDestroyed"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onRouteBuilt"
					sText += "\n" + CyTranslator().getText("[ICON_BULLET]", ()) + "onPlotRevealed"
					return sText
				elif iData2 == 1:
					return CyTranslator().getText("TXT_KEY_WB_PLAYER_DATA",())
				elif iData2 == 2:
					return CyTranslator().getText("TXT_KEY_WB_TEAM_DATA",())
				elif iData2 == 3:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_TECH",())
				elif iData2 == 4:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_PROJECT",())
				elif iData2 == 5:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_UNIT", ()) + " + " + CyTranslator().getText("TXT_KEY_CONCEPT_CITIES", ())
				elif iData2 == 6:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_PROMOTION",())
				elif iData2 == 7:
					return CyTranslator().getText("TXT_KEY_WB_CITY_DATA2",())
				elif iData2 == 8:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_BUILDING",())
				elif iData2 == 9:
					return "Platy Builder\nVersion: 4.17b"
				elif iData2 == 10:
					return CyTranslator().getText("TXT_KEY_CONCEPT_EVENTS",())
				elif iData2 == 11:
					return CyTranslator().getText("TXT_KEY_WB_RIVER_PLACEMENT",())
				elif iData2 == 12:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_IMPROVEMENT",())
				elif iData2 == 13:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_BONUS",())
				elif iData2 == 14:
					return CyTranslator().getText("TXT_KEY_WB_PLOT_TYPE",())
				elif iData2 == 15:
					return CyTranslator().getText("TXT_KEY_CONCEPT_TERRAIN",())
				elif iData2 == 16:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_ROUTE",())
				elif iData2 == 17:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_FEATURE",())
				elif iData2 == 18:
					return CyTranslator().getText("TXT_KEY_MISSION_BUILD_CITY",())
				elif iData2 == 19:
					return CyTranslator().getText("TXT_KEY_WB_ADD_BUILDINGS",())
				elif iData2 == 20:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_RELIGION",())
				elif iData2 == 21:
					return CyTranslator().getText("TXT_KEY_CONCEPT_CORPORATIONS",())
				elif iData2 == 22:
					return CyTranslator().getText("TXT_KEY_ESPIONAGE_CULTURE",())
				elif iData2 == 23:
					return CyTranslator().getText("TXT_KEY_PITBOSS_GAME_OPTIONS",())
				elif iData2 == 24:
					return CyTranslator().getText("TXT_KEY_WB_SENSIBILITY",())
				elif iData2 == 25:
					return CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_PLOT_EFFECT",())
				elif iData2 == 27:
					return CyTranslator().getText("TXT_KEY_WB_ADD_UNITS",())
				elif iData2 == 28:
					return CyTranslator().getText("TXT_KEY_WB_TERRITORY",())
				elif iData2 == 29:
					return CyTranslator().getText("TXT_KEY_WB_ERASE_ALL_PLOTS",())
				elif iData2 == 30:
					return CyTranslator().getText("TXT_KEY_WB_REPEATABLE",())
				elif iData2 == 31:
					return CyTranslator().getText("TXT_KEY_PEDIA_HIDE_INACTIVE", ())
				elif iData2 == 32:
					return CyTranslator().getText("TXT_KEY_WB_STARTING_PLOT", ())
				elif iData2 == 33:
					return CyTranslator().getText("TXT_KEY_INFO_SCREEN", ())
				elif iData2 == 34:
					return CyTranslator().getText("TXT_KEY_CONCEPT_TRADE", ())
			elif iData1 > 1029 and iData1 < 1040:
				if iData1 %2:
					return "-"
				return "+"
			elif iData1 == 1041:
				return CyTranslator().getText("TXT_KEY_WB_KILL",())
			elif iData1 == 1042:
				return CyTranslator().getText("TXT_KEY_MISSION_SKIP",())
			elif iData1 == 1043:
				if iData2 == 0:
					return CyTranslator().getText("TXT_KEY_WB_DONE",())
				elif iData2 == 1:
					return CyTranslator().getText("TXT_KEY_WB_FORTIFY",())
				elif iData2 == 2:
					return CyTranslator().getText("TXT_KEY_WB_WAIT",())
			elif iData1 == 6785:
				return CyGameTextMgr().getProjectHelp(iData2, False, CyCity())
			elif iData1 == 6787:
				return gc.getProcessInfo(iData2).getDescription()
			elif iData1 == 6788:
				if iData2 == -1:
					return CyTranslator().getText("TXT_KEY_CULTURELEVEL_NONE", ())
				return gc.getRouteInfo(iData2).getDescription()
			elif iData1 == 6789:
				if iData2 == -1:
					return CyTranslator().getText("TXT_KEY_CULTURELEVEL_NONE", ())
				return gc.getPlotEffectInfo(iData2).getDescription()
## City Hover Text ##
			elif iData1 > 7199 and iData1 < 7300:
				iPlayer = iData1 - 7200
				pPlayer = gc.getPlayer(iPlayer)
				pCity = pPlayer.getCity(iData2)
				if CyGame().GetWorldBuilderMode():
					sText = "<font=3>"
					if pCity.isCapital():
						sText += CyTranslator().getText("[ICON_STAR]", ())
					elif pCity.isGovernmentCenter():
						sText += CyTranslator().getText("[ICON_SILVER_STAR]", ())
					sText += u"%s: %d<font=2>" %(pCity.getName(), pCity.getPopulation())
					sTemp = ""
					if pCity.isConnectedToCapital(iPlayer):
						sTemp += CyTranslator().getText("[ICON_TRADE]", ())
					for i in xrange(gc.getNumReligionInfos()):
						if pCity.isHolyCityByType(i):
							sTemp += u"%c" %(gc.getReligionInfo(i).getHolyCityChar())
						elif pCity.isHasReligion(i):
							sTemp += u"%c" %(gc.getReligionInfo(i).getChar())

					for i in xrange(gc.getNumCorporationInfos()):
						if pCity.isHeadquartersByType(i):
							sTemp += u"%c" %(gc.getCorporationInfo(i).getHeadquarterChar())
						elif pCity.isHasCorporation(i):
							sTemp += u"%c" %(gc.getCorporationInfo(i).getChar())
					if len(sTemp) > 0:
						sText += "\n" + sTemp

					iMaxDefense = pCity.getTotalDefense(False)
					if iMaxDefense > 0:
						sText += u"\n%s: " %(CyTranslator().getText("[ICON_DEFENSE]", ()))
						iCurrent = pCity.getDefenseModifier(False)
						if iCurrent != iMaxDefense:
							sText += u"%d/" %(iCurrent)
						sText += u"%d%%" %(iMaxDefense)

					sText += u"\n%s: %d/%d" %(CyTranslator().getText("[ICON_FOOD]", ()), pCity.getFood(), pCity.growthThreshold())
					iFoodGrowth = pCity.foodDifference(True)
					if iFoodGrowth != 0:
						sText += u" %+d" %(iFoodGrowth)

					if pCity.isProduction():
						sText += u"\n%s:" %(CyTranslator().getText("[ICON_PRODUCTION]", ()))
						if not pCity.isProductionProcess():
							sText += u" %d/%d" %(pCity.getProduction(), pCity.getProductionNeeded())
							iProduction = pCity.getCurrentProductionDifference(False, True)
							if iProduction != 0:
								sText += u" %+d" %(iProduction)
						sText += u" (%s)" %(pCity.getProductionName())

					iGPRate = pCity.getGreatPeopleRate()
					iProgress = pCity.getGreatPeopleProgress()
					if iGPRate > 0 or iProgress > 0:
						sText += u"\n%s: %d/%d %+d" %(CyTranslator().getText("[ICON_GREATPEOPLE]", ()), iProgress, pPlayer.greatPeopleThreshold(False), iGPRate)

					sText += u"\n%s: %d/%d (%s)" %(CyTranslator().getText("[ICON_CULTURE]", ()), pCity.getCulture(iPlayer), pCity.getCultureThreshold(), gc.getCultureLevelInfo(pCity.getCultureLevel()).getDescription())

					lTemp = []
					for i in xrange(CommerceTypes.NUM_COMMERCE_TYPES):
						iAmount = pCity.getCommerceRateTimes100(i)
						if iAmount <= 0: continue
						sTemp = u"%d.%02d%c" %(pCity.getCommerceRate(i), pCity.getCommerceRateTimes100(i)%100, gc.getCommerceInfo(i).getChar())
						lTemp.append(sTemp)
					if len(lTemp) > 0:
						sText += "\n"
						for i in xrange(len(lTemp)):
							sText += lTemp[i]
							if i < len(lTemp) - 1:
								sText += ", "

					iMaintenance = pCity.getMaintenanceTimes100()
					if iMaintenance != 0:
						sText += "\n" + CyTranslator().getText("[COLOR_WARNING_TEXT]", ()) + CyTranslator().getText("INTERFACE_CITY_MAINTENANCE", ()) + " </color>"
						sText += u"-%d.%02d%c" %(iMaintenance/100, iMaintenance%100, gc.getCommerceInfo(CommerceTypes.COMMERCE_GOLD).getChar())

					lBuildings = []
					lWonders = []
					for i in xrange(gc.getNumBuildingInfos()):
						if pCity.isHasBuilding(i):
							Info = gc.getBuildingInfo(i)
							if isLimitedWonderClass(Info.getBuildingClassType()):
								lWonders.append(Info.getDescription())
							else:
								lBuildings.append(Info.getDescription())
					if len(lBuildings) > 0:
						lBuildings.sort()
						sText += "\n" + CyTranslator().getText("[COLOR_BUILDING_TEXT]", ()) + CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_BUILDING", ()) + ": </color>"
						for i in xrange(len(lBuildings)):
							sText += lBuildings[i]
							if i < len(lBuildings) - 1:
								sText += ", "
					if len(lWonders) > 0:
						lWonders.sort()
						sText += "\n" + CyTranslator().getText("[COLOR_SELECTED_TEXT]", ()) + CyTranslator().getText("TXT_KEY_CONCEPT_WONDERS", ()) + ": </color>"
						for i in xrange(len(lWonders)):
							sText += lWonders[i]
							if i < len(lWonders) - 1:
								sText += ", "
					sText += "</font>"
					return sText
## Religion Widget Text##
			elif iData1 == 7869:
				return CyGameTextMgr().parseReligionInfo(iData2, False)
## Building Widget Text##
			elif iData1 == 7870:
				return CyGameTextMgr().getBuildingHelp(iData2, False, False, False, None)
## Tech Widget Text##
			elif iData1 == 7871:
				if iData2 == -1:
					return CyTranslator().getText("TXT_KEY_CULTURELEVEL_NONE", ())
				return CyGameTextMgr().getTechHelp(iData2, False, False, False, False, -1)
## Civilization Widget Text##
			elif iData1 == 7872:
				iCiv = iData2 % 10000
				return CyGameTextMgr().parseCivInfos(iCiv, False)
## Promotion Widget Text##
			elif iData1 == 7873:
				return CyGameTextMgr().getPromotionHelp(iData2, False)
## Feature Widget Text##
			elif iData1 == 7874:
				if iData2 == -1:
					return CyTranslator().getText("TXT_KEY_CULTURELEVEL_NONE", ())
				iFeature = iData2 % 10000
				return CyGameTextMgr().getFeatureHelp(iFeature, False)
## Terrain Widget Text##
			elif iData1 == 7875:
				return CyGameTextMgr().getTerrainHelp(iData2, False)
## Leader Widget Text##
			elif iData1 == 7876:
				iLeader = iData2 % 10000
				return CyGameTextMgr().parseLeaderTraits(iLeader, -1, False, False)
## Improvement Widget Text##
			elif iData1 == 7877:
				if iData2 == -1:
					return CyTranslator().getText("TXT_KEY_CULTURELEVEL_NONE", ())
				return CyGameTextMgr().getImprovementHelp(iData2, False)
## Bonus Widget Text##
			elif iData1 == 7878:
				if iData2 == -1:
					return CyTranslator().getText("TXT_KEY_CULTURELEVEL_NONE", ())
				return CyGameTextMgr().getBonusHelp(iData2, False)
## Specialist Widget Text##
			elif iData1 == 7879:
				return CyGameTextMgr().getSpecialistHelp(iData2, False)
## Yield Text##
			elif iData1 == 7880:
				return gc.getYieldInfo(iData2).getDescription()
## Commerce Text##
			elif iData1 == 7881:
				return gc.getCommerceInfo(iData2).getDescription()
## Build Text##
			elif iData1 == 7882:
				return gc.getBuildInfo(iData2).getDescription()
## Effect Text ##
			elif iData1 == 7883:
				return gc.getPlotEffectInfo(iData2).getDescription()
## Trait Text ##
			elif iData1 == 7884:
				return CyGameTextMgr().parseTraits(iData2, -1, false)
## Flag Text ##
			elif iData1 == 7885:
				return gc.getFlagInfo(iData2).getDescription()
## Corporation Screen ##
			elif iData1 == 8201:
				return CyGameTextMgr().parseCorporationInfo(iData2, False)
## Military Screen ##
			elif iData1 == 8202:
				if iData2 == -1:
					return CyTranslator().getText("TXT_KEY_PEDIA_ALL_UNITS", ())
				return CyGameTextMgr().getUnitHelp(iData2, False, False, False, None)
			elif iData1 > 8299 and iData1 < 8400:
				iPlayer = iData1 - 8300
				pUnit = gc.getPlayer(iPlayer).getUnit(iData2)
				sText = CyGameTextMgr().getSpecificUnitHelp(pUnit, True, False)
				if CyGame().GetWorldBuilderMode():
					sText += "\n" + CyTranslator().getText("TXT_KEY_WB_UNIT", ()) + " ID: " + str(iData2)
					sText += "\n" + CyTranslator().getText("TXT_KEY_WB_GROUP", ()) + " ID: " + str(pUnit.getGroupID())
					sText += "\n" + "X: " + str(pUnit.getX()) + ", Y: " + str(pUnit.getY())
					sText += "\n" + CyTranslator().getText("TXT_KEY_WB_AREA_ID", ()) + ": "  + str(pUnit.plot().getArea())
				return sText
## Civics Screen ##
			elif iData1 == 8205 or iData1 == 8206:
				sText = CyGameTextMgr().parseCivicInfo(iData2, False, True, False)
				if gc.getCivicInfo(iData2).getUpkeep() > -1:
					sText += "\n" + gc.getUpkeepInfo(gc.getCivicInfo(iData2).getUpkeep()).getDescription()
				else:
					sText += "\n" + CyTranslator().getText("TXT_KEY_CIVICS_SCREEN_NO_UPKEEP", ())
				return sText
## Ultrapack ##

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getWidgetHelp']:
			modularReturn = module.getWidgetHelp(self, argsList)
			if len(modularReturn) > 0:
				return modularReturn

		## Modular Python End
		## *******************

		return u""

	def getUpgradePriceOverride(self, argsList):
		iPlayer, iUnitID, iUnitTypeUpgrade = argsList

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getUpgradePriceOverride']:
			modularReturn = module.getUpgradePriceOverride(self, argsList)
			if modularReturn > 0:
				return modularReturn

		## Modular Python End
		## *******************

		return -1	# Any value 0 or above will be used

	def getExperienceNeeded(self, argsList):
		# use this function to set how much experience a unit needs
		iLevel, iOwner = argsList
		gc 		= CyGlobalContext()
		iExperienceNeeded = 0

		# regular epic game experience
		if iLevel < 13:
			iExperienceNeeded = iLevel * iLevel + 1
		else:
			iExperienceNeeded = 13*13+1 + (iLevel-13)*25
		iExperienceNeeded = iExperienceNeeded*100

		iModifier = gc.getPlayer(iOwner).getLevelExperienceModifier()
		if (0 != iModifier):
			iExperienceNeeded += (iExperienceNeeded * iModifier + 99) / 100   # ROUND UP

		## *******************
		## Modular Python: ANW 29-may-2010
		## modified: estyles 24-Oct-2010

		for module in command['getExperienceNeeded']:
			modularReturn = module.getExperienceNeeded(self, argsList)
			if modularReturn > 0:
				return modularReturn

		## Modular Python End
		## *******************

		return iExperienceNeeded
