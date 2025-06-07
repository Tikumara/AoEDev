# Sid Meier's Civilization 4
# Copyright Firaxis Games 2006
#
# CvEventManager
# This class is passed an argsList from CvAppInterface.onEvent
# The argsList can contain anything from mouse location to key info
# The EVENTLIST that are being notified can be found

from CvPythonExtensions import *
import CvUtil
import CvScreensInterface
import CvDebugTools
import CvWBPopups
import PyHelpers
import Popup as PyPopup
import CvCameraControls
import CvTopCivs
import sys
import CvWorldBuilderScreen
import CvAdvisorUtils
import CvTechChooser
import pickle

import CvIntroMovieScreen
import CustomFunctions

import CvEspionageAdvisor
import ScenarioFunctions

#FfH: Card Game: begin
import CvSomniumInterface
import CvCorporationScreen
#FfH: Card Game: end

### GameFont Display
import GameFontDisplay
### GameFont Display

#FfH: Added by Kael 10/15/2008 for OOS Logging
import OOSLogger
#FfH: End Add

import Blizzards		#Added in Frozen: Blizzards: TC01

# Platy WB
import WBCityEditScreen
import WBUnitScreen
import WBPlayerScreen
import WBGameDataScreen
import WBPlotScreen
import CvPlatyBuilderScreen

## *******************
## Modular Python: ANW 16-feb-2010
##                     29-may-2010
##                     20-aug-2010
## ArcticNightWolf on CivFanatics
## ArcticNightWolf@gmail.com

# For dynamic plugin loading
import imp    # dynamic importing of libraries
#import glob   # Unix style pathname pattern expansion
import os     # Windows style pathname
import CvPath # path to current assets
import inspect

# Maps modules to the function name
# Syntax: {'functionName': [module1, module2]}
command = {}

# functionList is a list of strings of functions we will directly map
functionList = ['onMouseEvent', 'onKbdEvent', 'onModNetMessage', 'onInit', 'onUpdate', 'onUnInit', 'onSaveGame', 'onPreSave', 'onLoadGame', 'onBeginGameTurn',
 'onEndGameTurn', 'onBeginPlayerTurn', 'onEndPlayerTurn', 'onEndTurnReady', 'onCombatResult', 'onCombatLogCalc', 'onCombatLogHit',
 'onImprovementBuilt', 'onImprovementDestroyed', 'onRouteBuilt', 'onFirstContact', 'onCityBuilt', 'onCityRazed', 'onCityAcquired',
 'onCityAcquiredAndKept', 'onCityLost', 'onCultureExpansion', 'onCityGrowth', 'onCityDoTurn', 'onCityBuildingUnit', 'onCityBuildingBuilding',
 'onCityRename', 'onCityHurry', 'onSelectionGroupPushMission', 'onUnitMove', 'onUnitSetXY', 'onUnitCreated', 'onUnitBuilt', 'onUnitKilled',
 'onUnitLost', 'onUnitPromoted', 'onUnitSelected', 'onUnitRename', 'onUnitPillage', 'onUnitSpreadReligionAttempt', 'onUnitGifted',
 'onUnitBuildImprovement', 'onGoodyReceived', 'onGreatPersonBorn', 'onBuildingBuilt', 'onProjectBuilt', 'onTechAcquired', 'onTechSelected','onTraitGained','onTraitLost',
 'onReligionFounded', 'onReligionSpread', 'onReligionRemove', 'onCorporationFounded', 'onCorporationSpread', 'onCorporationRemove', 'onGoldenAge',
 'onEndGoldenAge', 'onChat', 'onVictory', 'onVassalState', 'onChangeWar', 'onSetPlayerAlive', 'onPlayerChangeStateReligion', 'onPlayerGoldTrade',
 'onWindowActivation', 'onGameUpdate', 'onGameStart', 'onGameEnd', 'onPlotRevealed', 'onPlotFeatureRemoved', 'onPlotPicked', 'onNukeExplosion', 'onGotoPlotSet']

## Modular Python End
## *******************

# globals
cf = CustomFunctions.CustomFunctions()
gc = CyGlobalContext()
localText = CyTranslator()
PyPlayer = PyHelpers.PyPlayer
PyInfo = PyHelpers.PyInfo
sf = ScenarioFunctions.ScenarioFunctions()

#FfH: Card Game: begin
cs = CvCorporationScreen.cs
#FfH: Card Game: end

Blizzards = Blizzards.Blizzards()		#Added in Frozen: Blizzards: TC01

#import GreyFoxCustom
import FoxDebug
import FoxTools
import time
from BasicFunctions import *

FoxGlobals = {
	"USE_DEBUG_WINDOW" 		: False,
	"USE_AIAUTOPLAY_SOUND" 	: True,
}
SoundSettings = {
	"SOUND_MASTER_VOLUME" 	: 0,
	"SOUND_SPEECH_VOLUME" 	: 0,
	"SOUND_MASTER_NO_SOUND" : False,
}


	# Import from BugUtil.py

# Import/hack from BugUtil.py. Maybe should be moved to a dedicated util file, but eh
deferredCallQueue = []
def deferCall(function, delay=0.0):
	"""
	Calls the given function during a future gameUpdate event after at least <delay> seconds.
	"""
	CvUtil.pyPrint('defer call start')
	global deferredCallQueue
	if delay < 0.0:
		delay = 0.0
	when = time.clock() + delay
	entry = (when, function)
	if deferredCallQueue:
		for i in range(len(deferredCallQueue)):
			if when < deferredCallQueue[i][0]:
				deferredCallQueue.insert(i, entry)
				return
	deferredCallQueue.append(entry)

def doDeferredCalls(argsList=None):
	"""
	Calls deferred calls whose timers have expired.
	"""
	global deferredCallQueue
	if deferredCallQueue:
		# insert a marker so that items added during this round of calls will be processed on the next round
		deferCall(None)
		while deferredCallQueue:
			when, func = deferredCallQueue[0]
			if func is None:
				del deferredCallQueue[0]
				break
			if when > time.clock():
				for i, (when, func) in enumerate(deferredCallQueue):
					if func is None:
						del deferredCallQueue[i]
						break
				break
			del deferredCallQueue[0]
			func()
			CvUtil.pyPrint('defer call EXECUTE')

# globals
###################################################
class CvEventManager:
	def __init__(self):
		#################### ON EVENT MAP ######################
		#print "EVENTMANAGER INIT"
		self.bCtrl = False
		self.bShift = False
		self.bAlt = False
		self.bAllowCheats = False
		self.pluginScan()

		# Dictionaries
		self.Defines			= {}
		self.Eras				= {}
		self.Techs				= {}
		self.Victories			= {}
		self.GameSpeeds			= {}
		self.GameOptions		= {}
		self.EventTriggers		= {}

		# Civs, etc
		self.Civilizations		= {}
		self.Leaders 			= {}
		self.LeaderStatus		= {}
		self.Traits 			= {}
		self.Civics 			= {}
		self.Religions			= {}
		self.Corporations		= {}
		self.Alignments			= {}

		# Buildings, etc
		self.Projects 			= {}
		self.Buildings 			= {}
		self.Specialists		= {}
		self.BuildingClasses	= {}
		self.Processes			= {}

		# Improvements, etc
		self.Builds				= {}
		self.Lairs 				= {}
		self.ManaNodes			= {}
		self.Improvements 		= {}
		self.CivImprovements	= {}
		self.UniqueImprovements	= {}

		# Terrain, etc
		self.Mana	 			= {}
		self.Terrain 			= {}
		self.Feature 			= {}
		self.Resources 			= {}
		self.WorldSizes			= {}
		self.Goodies			= {}

		# Units, etc
		self.Units 				= {}
		self.Heroes				= {}
		self.UnitAI				= {}
		self.Promotions 		= {}
		self.UnitClasses		= {}
		self.UnitCombats 		= {}
		self.GreatPeople 		= {}
		self.DamageTypes		= {}

		self.cf					= None
		self.Tools 				= None
		self.DbgWnd				= None
		self.LoadedData			= False

		# OnEvent Enums
		self.EventLButtonDown=1
		self.EventLcButtonDblClick=2
		self.EventRButtonDown=3
		self.EventBack=4
		self.EventForward=5
		self.EventKeyDown=6
		self.EventKeyUp=7

		self.__LOG_MOVEMENT = 0
		self.__LOG_BUILDING = 0
		self.__LOG_COMBAT = 0
		self.__LOG_CONTACT = 0
		self.__LOG_IMPROVEMENT =0
		self.__LOG_CITYLOST = 0
		self.__LOG_CITYBUILDING = 0
		self.__LOG_TECH = 0
		self.__LOG_UNITBUILD = 0
		self.__LOG_UNITKILLED = 0
		self.__LOG_UNITLOST = 0
		self.__LOG_UNITPROMOTED = 0
		self.__LOG_UNITSELECTED = 0
		self.__LOG_UNITPILLAGE = 0
		self.__LOG_GOODYRECEIVED = 0
		self.__LOG_GREATPERSON = 0
		self.__LOG_RELIGION = 0
		self.__LOG_RELIGIONSPREAD = 0
		self.__LOG_GOLDENAGE = 0
		self.__LOG_ENDGOLDENAGE = 0
		self.__LOG_WARPEACE = 0
		self.__LOG_PUSH_MISSION = 0

		## EVENTLIST
		self.EventHandlerMap = {
			'mouseEvent'					: self.onMouseEvent,
			'kbdEvent' 						: self.onKbdEvent,
			'ModNetMessage'					: self.onModNetMessage,
			'Init'							: self.onInit,
			'Update'						: self.onUpdate,
			'UnInit'						: self.onUnInit,
			'OnSave'						: self.onSaveGame,
			'OnPreSave'						: self.onPreSave,
			'OnLoad'						: self.onLoadGame,
			'GameStart'						: self.onGameStart,
			'GameEnd'						: self.onGameEnd,
			'plotRevealed' 					: self.onPlotRevealed,
			'plotFeatureRemoved' 			: self.onPlotFeatureRemoved,
			'plotPicked'					: self.onPlotPicked,
			'nukeExplosion'					: self.onNukeExplosion,
			'gotoPlotSet'					: self.onGotoPlotSet,
			'BeginGameTurn'					: self.onBeginGameTurn,
			'EndGameTurn'					: self.onEndGameTurn,
			'BeginPlayerTurn'				: self.onBeginPlayerTurn,
			'EndPlayerTurn'					: self.onEndPlayerTurn,
			'endTurnReady'					: self.onEndTurnReady,
			'combatResult' 					: self.onCombatResult,
			'combatLogCalc'	 				: self.onCombatLogCalc,
			'combatLogHit'					: self.onCombatLogHit,
			'improvementBuilt' 				: self.onImprovementBuilt,
			'improvementDestroyed' 			: self.onImprovementDestroyed,
			'routeBuilt' 					: self.onRouteBuilt,
			'firstContact' 					: self.onFirstContact,
			'cityBuilt' 					: self.onCityBuilt,
			'cityRazed'						: self.onCityRazed,
			'cityAcquired' 					: self.onCityAcquired,
			'cityAcquiredAndKept' 			: self.onCityAcquiredAndKept,
			'cityLost'						: self.onCityLost,
			'cultureExpansion' 				: self.onCultureExpansion,
			'cityGrowth' 					: self.onCityGrowth,
			'cityDoTurn' 					: self.onCityDoTurn,
			'cityBuildingUnit'				: self.onCityBuildingUnit,
			'cityBuildingBuilding'			: self.onCityBuildingBuilding,
			'cityRename'					: self.onCityRename,
			'cityHurry'						: self.onCityHurry,
			'selectionGroupPushMission'		: self.onSelectionGroupPushMission,
			'unitMove' 						: self.onUnitMove,
			'unitSetXY' 					: self.onUnitSetXY,
			'unitCreated' 					: self.onUnitCreated,
			'unitBuilt' 					: self.onUnitBuilt,
			'unitKilled'					: self.onUnitKilled,
			'unitLost'						: self.onUnitLost,
			'unitPromoted'					: self.onUnitPromoted,
			'unitSelected'					: self.onUnitSelected,
			'UnitRename'					: self.onUnitRename,
			'unitPillage'					: self.onUnitPillage,
			'unitSpreadReligionAttempt'		: self.onUnitSpreadReligionAttempt,
			'unitGifted'					: self.onUnitGifted,
			'unitBuildImprovement'			: self.onUnitBuildImprovement,
			'goodyReceived'					: self.onGoodyReceived,
			'greatPersonBorn'	  			: self.onGreatPersonBorn,
			'buildingBuilt' 				: self.onBuildingBuilt,
			'projectBuilt' 					: self.onProjectBuilt,
			'techAcquired'					: self.onTechAcquired,
			'techSelected'					: self.onTechSelected,
			'traitGained'					: self.onTraitGained,
			'traitLost'						: self.onTraitLost,
			'religionFounded'				: self.onReligionFounded,
			'religionSpread'				: self.onReligionSpread,
			'religionRemove'				: self.onReligionRemove,
			'corporationFounded'			: self.onCorporationFounded,
			'corporationSpread'				: self.onCorporationSpread,
			'corporationRemove'				: self.onCorporationRemove,
			'goldenAge'						: self.onGoldenAge,
			'endGoldenAge'					: self.onEndGoldenAge,
			'chat' 							: self.onChat,
			'victory'						: self.onVictory,
			'vassalState'					: self.onVassalState,
			'changeWar'						: self.onChangeWar,
			'setPlayerAlive'				: self.onSetPlayerAlive,
			'playerChangeStateReligion'		: self.onPlayerChangeStateReligion,
			'playerGoldTrade'				: self.onPlayerGoldTrade,
			'windowActivation'				: self.onWindowActivation,
			'gameUpdate'					: self.onGameUpdate,		# sample generic event
			'combatHit'					: '', #These are used by UnitStatistics.
			'airIntercept'					: '',
			'combatBegin'					: '',
			'combatWithdrawal'					: '',
			'airStrikeHit'					: '',
			'unitUpgraded'					: '',
			'spellCast'					: '',
			'unitConverted'					: '',
			'combatHit'					: '',
		}

		################## Events List ###############################
		#
		# Dictionary of Events, indexed by EventID (also used at popup context id)
		#   entries have name, beginFunction, applyFunction [, randomization weight...]
		#
		# Normal events first, random events after
		#
		################## Events List ###############################
		self.Events={
			CvUtil.EventEditCityName : ('EditCityName', self.__eventEditCityNameApply, self.__eventEditCityNameBegin),
			CvUtil.EventEditCity : ('EditCity', self.__eventEditCityApply, self.__eventEditCityBegin),
			CvUtil.EventPlaceObject : ('PlaceObject', self.__eventPlaceObjectApply, self.__eventPlaceObjectBegin),
			CvUtil.EventAwardTechsAndGold: ('AwardTechsAndGold', self.__eventAwardTechsAndGoldApply, self.__eventAwardTechsAndGoldBegin),
			CvUtil.EventEditUnitName : ('EditUnitName', self.__eventEditUnitNameApply, self.__eventEditUnitNameBegin),
			CvUtil.EventWBAllPlotsPopup : ('WBAllPlotsPopup', self.__eventWBAllPlotsPopupApply, self.__eventWBAllPlotsPopupBegin),
			CvUtil.EventWBLandmarkPopup : ('WBLandmarkPopup', self.__eventWBLandmarkPopupApply, self.__eventWBLandmarkPopupBegin),
			CvUtil.EventWBScriptPopup : ('WBScriptPopup', self.__eventWBScriptPopupApply, self.__eventWBScriptPopupBegin),
			CvUtil.EventWBStartYearPopup : ('WBStartYearPopup', self.__eventWBStartYearPopupApply, self.__eventWBStartYearPopupBegin),
			CvUtil.EventShowWonder: ('ShowWonder', self.__eventShowWonderApply, self.__eventShowWonderBegin),
			CvUtil.EventSetTurnsAutoPlayPopup : ('SetTurnsAutoPlayPopup', self.__eventSetTurnsAutoPlayApply, self.__eventSetTurnsAutoPlayBegin),
			CvUtil.EventSetUnitPerTilePopup : ('SetUnitPerTilePopup', self.__eventSetUnitPerTileApply, self.__eventSetUnitPerTileBegin),
			CvUtil.EventCheat: ('TriggerRandEvent', self.__eventCheatEventApply, self.__eventCheatEventBegin),
		
## Platy Builder ##
			CvUtil.EventWBLandmarkPopup : ('WBLandmarkPopup', self.__eventWBLandmarkPopupApply, self.__eventWBScriptPopupBegin),
			CvUtil.EventShowWonder: ('ShowWonder', self.__eventShowWonderApply, self.__eventShowWonderBegin),
			1111 : ('WBPlayerScript', self.__eventWBPlayerScriptPopupApply, self.__eventWBScriptPopupBegin),
			2222 : ('WBCityScript', self.__eventWBCityScriptPopupApply, self.__eventWBScriptPopupBegin),
			3333 : ('WBUnitScript', self.__eventWBUnitScriptPopupApply, self.__eventWBScriptPopupBegin),
			4444 : ('WBGameScript', self.__eventWBGameScriptPopupApply, self.__eventWBScriptPopupBegin),
			5555 : ('WBPlotScript', self.__eventWBPlotScriptPopupApply, self.__eventWBScriptPopupBegin),
## Platy Builder ##
		
		}
## FfH Card Game: begin
		self.Events[CvUtil.EventSelectSolmniumPlayer] = ('selectSolmniumPlayer', self.__EventSelectSolmniumPlayerApply, self.__EventSelectSolmniumPlayerBegin)
		self.Events[CvUtil.EventSolmniumAcceptGame] = ('solmniumAcceptGame', self.__EventSolmniumAcceptGameApply, self.__EventSolmniumAcceptGameBegin)
		self.Events[CvUtil.EventSolmniumConcedeGame] = ('solmniumConcedeGame', self.__EventSolmniumConcedeGameApply, self.__EventSolmniumConcedeGameBegin)
## FfH Card Game: end

#################### EVENT STARTERS ######################
	def handleEvent(self, argsList):
		'EventMgr entry point'
		# extract the last 6 args in the list, the first arg has already been consumed
		self.origArgsList = argsList	# point to original
		tag = argsList[0]				# event type string
		idx = len(argsList)-6
		bDummy = False
		self.bDbg, bDummy, self.bAlt, self.bCtrl, self.bShift, self.bAllowCheats = argsList[idx:]
		ret = 0
		if self.EventHandlerMap.has_key(tag):
			fxn = self.EventHandlerMap[tag]
			ret = fxn(argsList[1:idx])
		return ret

#################### EVENT APPLY ######################
	def beginEvent( self, context, argsList=-1 ):
		'Begin Event'
		entry = self.Events[context]
		return entry[2]( argsList )

	def applyEvent( self, argsList ):
		'Apply the effects of an event '
		context, playerID, netUserData, popupReturn = argsList

		if context == CvUtil.PopupTypeEffectViewer:
			return CvDebugTools.g_CvDebugTools.applyEffectViewer( playerID, netUserData, popupReturn )

		entry = self.Events[context]

		if ( context not in CvUtil.SilentEvents ):
			self.reportEvent(entry, context, (playerID, netUserData, popupReturn) )
		return entry[1]( playerID, netUserData, popupReturn )   # the apply function

	def reportEvent(self, entry, context, argsList):
		'Report an Event to Events.log '
		if (CyGame().getActivePlayer() != -1):
			message = "DEBUG Event: %s (%s)" %(entry[0], CyGlobalContext().getActivePlayer().getName())
			CyInterface().addImmediateMessage(message,"")
			CvUtil.pyPrint(message)
		return 0

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
	def onKbdEvent(self, argsList):
		'keypress handler - return 1 if the event was consumed'

		eventType,key,mx,my,px,py = argsList
		game 		= CyGame()
		map 		= CyMap()
		cf			= self.cf

		if (self.bAllowCheats):
			# notify debug tools of input to allow it to override the control
			argsList = (eventType,key,self.bCtrl,self.bShift,self.bAlt,mx,my,px,py,game.isNetworkMultiPlayer())
			if ( CvDebugTools.g_CvDebugTools.notifyInput(argsList) ):
				return 0

		if ( eventType == self.EventKeyDown ):
			theKey=int(key)
						
### GameFont Display
			if theKey == int(InputTypes.KB_F1) and self.bShift and self.bCtrl:
				GameFontDisplay.GameFontDisplay().interfaceScreen()
				return 1
### GameFont Display

#FfH: Added by Kael 07/05/2008
			if (theKey == int(InputTypes.KB_LEFT)):
				if self.bCtrl:
						CyCamera().SetBaseTurn(CyCamera().GetBaseTurn() - 45.0)
						return 1
				elif self.bShift:
						CyCamera().SetBaseTurn(CyCamera().GetBaseTurn() - 10.0)
						return 1

			if (theKey == int(InputTypes.KB_RIGHT)):
					if self.bCtrl:
							CyCamera().SetBaseTurn(CyCamera().GetBaseTurn() + 45.0)
							return 1
					elif self.bShift:
							CyCamera().SetBaseTurn(CyCamera().GetBaseTurn() + 10.0)
							return 1
#FfH: End Add
			if (self.bAllowCheats):
				# Shift E (Debug - Trigger an Event)
				if (theKey== int(InputTypes.KB_E)):
					if(self.bShift):
						CvDebugTools.CvDebugTools().cheatEvents2()
						return 1

			if (self.bAllowCheats):
				# Shift Y (Debug - Remove AI Units)
				if (theKey== int(InputTypes.KB_Y)):
					if(self.bShift):
						CvDebugTools.CvDebugTools().debugRemoveAIUnits()
						return 1

			CvCameraControls.g_CameraControls.handleInput( theKey )

			if (self.bAllowCheats):
				# Shift - T (Debug - No MP)
				if (theKey == int(InputTypes.KB_T)):
					if ( self.bShift ):
						self.beginEvent(CvUtil.EventAwardTechsAndGold)
						#self.beginEvent(CvUtil.EventCameraControlPopup)
						return 1

				elif (theKey == int(InputTypes.KB_W)):
					if ( self.bShift and self.bCtrl):
						self.beginEvent(CvUtil.EventShowWonder)
						return 1

				# Shift - ] (Debug - currently mouse-overd unit, health += 10
				elif (theKey == int(InputTypes.KB_LBRACKET) and self.bShift ):
					unit = map.plot(px, py).getUnit(0)
					if ( not unit.isNone() ):
						d = min( unit.maxHitPoints()-1, unit.getDamage() + 10 )
						unit.setDamage( d, PlayerTypes.NO_PLAYER )

				# Shift - [ (Debug - currently mouse-overd unit, health -= 10
				elif (theKey == int(InputTypes.KB_RBRACKET) and self.bShift ):
					unit = map.plot(px, py).getUnit(0)
					if ( not unit.isNone() ):
						d = max( 0, unit.getDamage() - 10 )
						unit.setDamage( d, PlayerTypes.NO_PLAYER )

				elif (theKey == int(InputTypes.KB_F1)):
					if ( self.bShift ):
						CvScreensInterface.replayScreen.showScreen(False)
						return 1
					# don't return 1 unless you want the input consumed

				elif (theKey == int(InputTypes.KB_F2)):
					if ( self.bShift ):
						import CvDebugInfoScreen
						CvScreensInterface.showDebugInfoScreen()
						return 1

				elif (theKey == int(InputTypes.KB_F3)):
					if ( self.bShift ):
						CvScreensInterface.showDanQuayleScreen(())
						return 1

				elif (theKey == int(InputTypes.KB_F4)):
					if ( self.bShift ):
						CvScreensInterface.showUnVictoryScreen(())
						return 1


			if (self.bAllowCheats or game.isMPOption(MultiplayerOptionTypes.MPOPTION_ENABLE_AUTOPLAY)):
				if (theKey == int(InputTypes.KB_X) and self.bShift and self.bCtrl):
					CyMessageControl().sendModNetMessage(CvUtil.AutoPlay, 1, -1, -1, -1)
				elif (theKey == int(InputTypes.KB_Z) and self.bShift and self.bCtrl):
					if game.getAIAutoPlay() > 0:
						CyMessageControl().sendModNetMessage(CvUtil.AutoPlay, 0, -1, -1, -1)
					else:
						cf.showAutoPlayPopup()

			if (theKey == int(InputTypes.KB_U) and self.bShift):
				if (not game.isUPTLock() or self.bAllowCheats):
					cf.showUnitPerTilePopup()

# Grey Fox Speed Tweaks: START
			if ( self.bShift ):
				if (theKey == int(InputTypes.KB_C)):
					if FoxGlobals["USE_DEBUG_WINDOW"]:
						self.DbgWnd.updateDebugPanel()
# END

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onKbdEvent']:
			module.onKbdEvent(self, argsList)

		## Modular Python End
		## *******************

		return 0
		
		
	def __eventCheatEventApply(self, playerID, netUserData, popupReturn):
		'Cheat Event Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyCheatEvent( (popupReturn) )
			
			
	def onModNetMessage(self, argsList):
		'Called whenever CyMessageControl().sendModNetMessage() is called - this is all for you modders!'
		gc = CyGlobalContext()
		game = CyGame()
		iData1, iData2, iData3, iData4, iData5 = argsList

#FfH Card Game: begin
#		print("Modder's net message!")
#		CvUtil.pyPrint( 'onModNetMessage' )
		if iData1 == CvUtil.Somnium : # iData1 == 0 : Somnium message, iData2 = function, iData3 to iData5 = parameters
			if iData2 == 0:
				if (iData3 == game.getActivePlayer()):
					self.__EventSelectSolmniumPlayerBegin()
			elif iData2 == 1:
				if (iData4 == game.getActivePlayer()):
					self.__EventSolmniumConcedeGameBegin((iData3, iData4))
			else :
				cs.applyAction(iData2, iData3, iData4, iData5)
# FfH Card Game: end
		elif iData1 == CvUtil.CivSelector:  #iData1==1 : CivSelect message,  iData2 = iCiv, iData3 = bAIPlayable, iData4 = bPlayable
			gc.getCivilizationInfo(iData2).setAIPlayable(iData3)
			gc.getCivilizationInfo(iData2).setPlayable(iData4)

		elif iData1 == CvUtil.AutoPlay:	#iData1 == 2: AutoPlay Config, iData2 = SetTurns
			game.setAIAutoPlay(iData2)

		elif iData1 == CvUtil.UPT: #iData1 == 3: UPT Config, iData2 = SetUPT, iData3 = bLock
			game.setUPT(iData2)
			if (iData3):
				game.setUPTLock(True)

		elif iData1 == CvUtil.reassignPlayer:
						game.reassignPlayerAdvanced(iData2, iData3, -1)

		elif iData1 == 100:
			iButtonId		= iData2
			iPlayer			= iData3
			gc				= CyGlobalContext()
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iPlayer)
			# List should be the same as lTraits in CvEventManager, onBeginPlayerTurn, Trait Adaptive part.
			lDirtyTraits = [git("TRAIT_AGGRESSIVE"),git("TRAIT_ARCANE"),git("TRAIT_CHARISMATIC"),git("TRAIT_CREATIVE"),git("TRAIT_EXPANSIVE"),git("TRAIT_FINANCIAL"),git("TRAIT_INDUSTRIOUS"),git("TRAIT_ORGANIZED"),git("TRAIT_PHILOSOPHICAL"),git("TRAIT_RAIDERS"),git("TRAIT_SPIRITUAL")]
			lTraits = []
			for i in lDirtyTraits:
				if not pPlayer.hasTrait(i):
					lTraits.append(i)
			iTrait = lTraits[iButtonId]
			if not gc.isNoCrash():
				pPlayer.setHasTrait((iTrait),True,-1,True,True)
			else:
				pPlayer.setHasTrait((iTrait),True)

		elif iData1 == 101:
			iButtonId	= iData2
			iPlayer		= iData3
			iElection	= iData4
			gc			= CyGlobalContext()
			git			= gc.getInfoTypeForString
			pPlayer		= gc.getPlayer(iPlayer)
			iRnd		= CyGame().getSorenRandNum(100, "Republic Election")
			iShift		= iButtonId
			if iRnd < 20 and iButtonId != 2: # 20% to fail if someone is supported
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_EVENT_REPUBLIC_ELECTION_OPPOSITION_PARTY_WINS", ()),'',3,'Art/Interface/Buttons/Civics/Republic.dds',git("COLOR_RED"),pPlayer.getCapitalCity().getX(),pPlayer.getCapitalCity().getY(),True,True)
				return
			lRepublicTraits		= [git("TRAIT_AGGRESSIVE_REPUBLIC"),git("TRAIT_DEFENDER_REPUBLIC"),git("TRAIT_FINANCIAL_REPUBLIC"),git("TRAIT_EXPANSIVE_REPUBLIC"),git("TRAIT_SPIRITUAL_REPUBLIC"),git("TRAIT_ORGANIZED_REPUBLIC"),git("TRAIT_INDUSTRIOUS_REPUBLIC"),git("TRAIT_PHILOSOPHICAL_REPUBLIC")]
			lTraits				= [git("TRAIT_AGGRESSIVE"),git("TRAIT_DEFENDER"),git("TRAIT_FINANCIAL"),git("TRAIT_EXPANSIVE"),git("TRAIT_SPIRITUAL"),git("TRAIT_ORGANIZED"),git("TRAIT_INDUSTRIOUS"),git("TRAIT_PHILOSOPHICAL")]
			lRepublicTraitsText = ["TXT_KEY_EVENT_REPUBLIC_ELECTION_HAWK_WINS","TXT_KEY_EVENT_REPUBLIC_ELECTION_DOVE_WINS","TXT_KEY_EVENT_REPUBLIC_ELECTION_LANDOWNER_WINS","TXT_KEY_EVENT_REPUBLIC_ELECTION_PEASANT_WINS","TXT_KEY_EVENT_REPUBLIC_ELECTION_CHURCH_WINS","TXT_KEY_EVENT_REPUBLIC_ELECTION_STATE_WINS","TXT_KEY_EVENT_REPUBLIC_ELECTION_LABOR_WINS","TXT_KEY_EVENT_REPUBLIC_ELECTION_ACADEMIA_WINS"]
			lRepublicAltText	= ["TXT_KEY_EVENT_REPUBLIC_ELECTION_HAWK_WINS_ALREADY_AGGRESSIVE","TXT_KEY_EVENT_REPUBLIC_ELECTION_DOVE_WINS_ALREADY_DEFENSIVE","TXT_KEY_EVENT_REPUBLIC_ELECTION_LANDOWNER_WINS_ALREADY_FINANCIAL","TXT_KEY_EVENT_REPUBLIC_ELECTION_PEASANT_WINS_ALREADY_EXPANSIVE","TXT_KEY_EVENT_REPUBLIC_ELECTION_CHURCH_WINS_ALREADY_SPIRITUAL","TXT_KEY_EVENT_REPUBLIC_ELECTION_STATE_WINS_ALREADY_ORGANIZED","TXT_KEY_EVENT_REPUBLIC_ELECTION_LABOR_WINS_ALREADY_INDUSTRIOUS","TXT_KEY_EVENT_REPUBLIC_ELECTION_ACADEMIA_WINS_ALREADY_PHILOSOPHICAL"]
			if iRnd < 50 and iButtonId == 2: # 50/50 for every party to win if no one is supported
				iShift = 0
			elif iButtonId == 2:
				iShift = 1
			iElectionIndex = iElection * 2 + iShift # Based on Election Type and Button pressed: Hawk = 0, Dove = 1, Landowner = 2, Pesants = 3, Church = 4, State = 5, Labor = 6, Academia = 7
			bRepeatTrait = 0
			iTrait = lTraits[iElectionIndex]
			iRepublicTrait = lRepublicTraits[iElectionIndex]
			if pPlayer.hasTrait(iTrait) or pPlayer.hasTrait(iRepublicTrait):
				bRepeatTrait = 1
			if bRepeatTrait == 0: # Trait Rewards
				if not gc.isNoCrash():
					pPlayer.setHasTrait((iRepublicTrait),True,-1,True,True)
				else:
					pPlayer.setHasTrait((iRepublicTrait),True)
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText(lRepublicTraitsText[iElectionIndex], ()),'',3,'Art/Interface/Buttons/Civics/Republic.dds',git("COLOR_GREEN"),pPlayer.getCapitalCity().getX(),pPlayer.getCapitalCity().getY(),True,True)
			else: # Alt Rewards
				if iElectionIndex == 0: # Hawk wins
					pPlayer.initUnit(git('UNIT_COMMANDER'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				if iElectionIndex == 1: # Dove wins
					for iLoopPlayer in range(gc.getMAX_CIV_PLAYERS()):
						loopPlayer = gc.getPlayer(iLoopPlayer)
						if loopPlayer.isAlive():
							if loopPlayer.getTeam() != pPlayer.getTeam():
								loopPlayer.AI_changeAttitudeExtra(iPlayer, 3)
								pPlayer.AI_changeAttitudeExtra(iLoopPlayer, 3)
				if iElectionIndex == 2: # Landowner wins
					pPlayer.initUnit(git('UNIT_MERCHANT'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				if iElectionIndex == 3: # Pesants win
					(loopCity, iter) = pPlayer.firstCity(False)
					while(loopCity):
						loopCity.changeHappinessTimer(30)
						loopCity.changeEspionageHealthCounter(-5)
						(loopCity, iter) = pPlayer.nextCity(iter, False)
				if iElectionIndex == 4: # Church wins
					pPlayer.initUnit(git('UNIT_PROPHET'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				if iElectionIndex == 5: # State wins
					pPlayer.changeGoldenAgeTurns(CyGame().goldenAgeLength())
				if iElectionIndex == 6: # Labor wins
					pPlayer.initUnit(git('UNIT_ENGINEER'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				if iElectionIndex == 7: # Academia wins
					pPlayer.initUnit(git('UNIT_SCIENTIST'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText(lRepublicAltText[iElectionIndex], ()),'',3,'Art/Interface/Buttons/Civics/Republic.dds',git("COLOR_GREEN"),pPlayer.getCapitalCity().getX(),pPlayer.getCapitalCity().getY(),True,True)

		elif iData1 == 102:
			iPlayer = iData2
			pPlayer = gc.getPlayer(iPlayer)
			git				= gc.getInfoTypeForString
			pBestPlot = -1
			iBestPlot = -1
			for i in range (CyMap().numPlots()):
				pPlot = CyMap().plotByIndex(i)
				iPlot = -1
				if not pPlot.isWater():
					if pPlot.getNumUnits() == 0:
						if not pPlot.isCity():
							if not pPlot.isImpassable():
								iPlot = CyGame().getSorenRandNum(1000, "Add Unit")
								if pPlot.area().getNumTiles() < 8:
									iPlot += 1000
								if not pPlot.isOwned():
									iPlot += 1000
								if iPlot > iBestPlot:
									iBestPlot = iPlot
									pBestPlot = pPlot
			if iBestPlot != -1:
				containerUnit = -1
				for i in range(pBestPlot.getNumUnits()):
					if pBestPlot.getUnit(i).getUnitType() == git('EQUIPMENT_CONTAINER'):
						containerUnit = pBestPlot.getUnit(i)
				if containerUnit == -1:
					containerUnit = gc.getPlayer(gc.getORC_PLAYER()).initUnit(git('EQUIPMENT_CONTAINER'), pBestPlot.getX(), pBestPlot.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				containerUnit.setHasPromotion(git('PROMOTION_GODSLAYER'), True)
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_EXPLORE_LAIR_TREASURE",()),'',1,'Art/Interface/Buttons/Equipment/Treasure.dds',ColorTypes(8),containerUnit.getX(),containerUnit.getY(),True,True)
				iTeam = pPlayer.getTeam()
				signText = CvUtil.convertToStr(CyTranslator().getText("TXT_KEY_EQUIPMENT_GODSLAYER", ()))
				pBestPlot.setRevealed(iTeam, True, False, TeamTypes.NO_TEAM)
				CyCamera().JustLookAtPlot(pBestPlot)
				CyEngine().addSign(pBestPlot, iPlayer, signText)

		elif iData1 == 103:
			iButtonId		= iData2
			iPlayer			= iData3
			gc				= CyGlobalContext()
			git				= gc.getInfoTypeForString
			cf				= CustomFunctions.CustomFunctions()
			pPlayer = gc.getPlayer(iPlayer)
			lDemonLordsList= [git("LEADER_HYBOREM")]
			lDemonLordsTraitList=["TRAIT_PACT_HYBOREM"]
			if (git("MODULE_IMPORTANT_LEADERS")!=-1):
				lDemonLordsList=lDemonLordsList+[git("LEADER_MERESIN"),git("LEADER_OUZZA"),git("LEADER_STATIUS"),git("LEADER_SALLOS"),git("LEADER_LETHE"),git("LEADER_JUDECCA")]
				lDemonLordsTraitList=lDemonLordsTraitList+["TRAIT_PACT_MERESIN","TRAIT_PACT_OUZZA","TRAIT_PACT_STATIUS","TRAIT_PACT_SALLOS","TRAIT_PACT_LETHE","TRAIT_PACT_JUDECCA"]
					
			lDemonLordsToSpawn = []
			lDemonLordsTraitToSpawn = []
			for iDemonLord in range(len(lDemonLordsList)):
				if not CyGame().isLeaderEverActive(lDemonLordsList[iDemonLord]):
					lDemonLordsToSpawn.append(lDemonLordsList[iDemonLord])
					lDemonLordsTraitToSpawn.append(lDemonLordsTraitList[iDemonLord])
			iCounter	= 0
			iCounterTrait=0
			iLeader		= -1
			bSwap		= False
			for i in lDemonLordsToSpawn:
				if iButtonId == iCounter:
					iLeader = i
					cf.spawnDemonLord(iLeader,iPlayer)
					pPlayer.setHasTrait(git(lDemonLordsTraitToSpawn[iCounterTrait]),True)
					return
				else:
					iCounter += 1
				if iButtonId == iCounter:
					iLeader = i
					cf.spawnDemonLord(iLeader,iPlayer,True)
					pPlayer.setHasTrait(git(lDemonLordsTraitToSpawn[iCounterTrait]),True)
					return
				else:
					iCounter += 1
				iCounterTrait+=1
		elif iData1 == 104:
			iButtonId	= iData2
			iPlayer		= iData3
			pPlayer		= gc.getPlayer(iPlayer)
			iCity		= iButtonId + 1
			pCity		= cf.getAshenVeilCity(iCity)
			pPlayer.acquireCity(pCity,False,False)

		elif iData1 == 105:
			iButtonId	= iData2
			iPlayer		= iData3
			pPlayer		= gc.getPlayer(iPlayer)
			git			= gc.getInfoTypeForString
			pCapital	= pPlayer.getCapitalCity()
			if iButtonId == 0:
				pPlayer.setFeatAccomplished(FeatTypes.FEAT_VISIT_MIRROR_OF_HEAVEN, False)
				return
			if iButtonId == 1:
				newUnit = pPlayer.initUnit(git('UNIT_LIGHTBRINGER'), pCapital.getX(), pCapital.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				newUnit.setName(CyTranslator().getText("TXT_KEY_EVENT_MALAKIM_MIRROR_2_HERMIT_NAME",()))
				newUnit.setHasPromotion(git('PROMOTION_HERO'), True)
				newUnit.setHasPromotion(git('PROMOTION_MOBILITY1'), True)
			if iButtonId == 2:
				pCapital.setNumRealBuilding(git('BUILDING_MALAKIM_TEMPLE_MIRROR'), 1)

		elif iData1 == 106:
			iButtonId	= iData2
			iCaster		= iData3
			iPlayer		= iData4
			pPlayer		= gc.getPlayer(iPlayer)
			pCaster		= pPlayer.getUnit(iCaster)
			pPlot		= pCaster.plot()
			git			= gc.getInfoTypeForString
			if iButtonId == 2:
				gc.getGame().setGlobalFlag(git("FLAG_FOXFORD_FIRST_TIME"),False)
				return
			iRnd		= CyGame().getSorenRandNum(100, "Foxford General Roll")
			if iButtonId == 0:
				pCaster.setHasPromotion(git('PROMOTION_ADVENTURER'), True)
				pCaster.changeExperienceTimes100(500, -1, False, False, False)
				iGold = 20 + CyGame().getSorenRandNum(10, "Foxford Gold Roll")
				pPlayer.changeGold(iGold)
				if iRnd < 15:
					CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_EVENT_FOXFORD_WOLFKILLED", ()),'',3,'Art/Interface/Buttons/Promotions/Werewolf.dds',git("COLOR_RED"),pPlot.getX(),pPlot.getY(),True,True)
					pCaster.kill(False,-1)
				return
			if iButtonId == 1:
				pCaster.setHasPromotion(git('PROMOTION_WEREWOLF'), True)
				CyGame().setPlotExtraYield (pPlot.getX(),pPlot.getY(), git("YIELD_COMMERCE"), -3)
				pPlayer.setHasFlag(git("FLAG_FOXFORD_RAZED"),True)
				CyEngine().removeLandmark(pPlot)
				if iRnd < 33:
					CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_EVENT_FOXFORD_LYNCHED", ()),'',3,'Art/Interface/Buttons/Actions/Pillage.dds',git("COLOR_RED"),pPlot.getX(),pPlot.getY(),True,True)
					pCaster.kill(False,-1)

		elif iData1 == 107:
			iButtonId	= iData2
			iUnit		= iData3
			iPlayer		= iData4
			pUnit		= gc.getPlayer(iPlayer).getUnit(iUnit)
			if iButtonId == 0:
				iBestValue = 0
				pBestPlot = -1
				for i in xrange (CyMap().numPlots()):
					iValue = 0
					pPlot = CyMap().plotByIndex(i)
					if not pPlot.isWater() and not pPlot.isPeak() and pPlot.getNumUnits() == 0:
						iValue = CyGame().getSorenRandNum(1000, "Portal")
						if not pPlot.isOwned():
							iValue += 1000
						if iValue > iBestValue:
							iBestValue = iValue
							pBestPlot = pPlot
				if pBestPlot != -1:
					pUnit.setXY(pBestPlot.getX(), pBestPlot.getY(), False, True, True)
					CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_EXPLORE_LAIR_PORTAL",()),'',1,'Art/Interface/Buttons/Spells/Explore Lair.dds',ColorTypes(8),pBestPlot.getX(),pBestPlot.getY(),True,True)

		elif iData1 == 108:
			iButtonId		= iData2
			iUnit			= iData3
			iPlayer			= iData4
			pType			= iData5
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iPlayer)
			pUnit			= pPlayer.getUnit(iUnit)
			pPlot			= pUnit.plot()
			pNewPlot		= findClearPlot(-1, pPlot)
			bPlayer			= gc.getPlayer(gc.getORC_PLAYER())
			pPlayer1		= bPlayer
			pPlayer2		= bPlayer
			iCount1			= 3
			iCount2			= 3
			pPlot1			= pNewPlot
			pPlot2			= pNewPlot
			bBronze			= False
			bPoison			= False
			if pType == 1:		# DwarfVsLizard
				pUnitType1	= git("UNIT_AXEMAN")
				pUnitType2	= git("UNIT_LIZARDMAN")
			elif pType == 2:	# RedVsYellow
				pUnitType1	= git("UNIT_ARCHER_SCORPION_CLAN")
				pUnitType2	= git("UNIT_GOBLIN_MURIS_CLAN")
			if bPlayer.isHasTech(git('TECH_BRONZE_WORKING')):
				bBronze = True
			if bPlayer.isHasTech(git('TECH_HUNTING')):
				bPoison = True
			if iButtonId == 0:
				pPlayer1	= pPlayer
				iCount1		= 2
				pPlot1		= pPlot
			elif iButtonId == 1:
				pPlayer2	= pPlayer
				iCount2		= 2
				pPlot2		= pPlot
			if pNewPlot != -1:
				for i in xrange(iCount1):
					newUnitFirst = pPlayer1.initUnit(pUnitType1, pPlot1.getX(), pPlot1.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					if pType == 1:
						newUnitFirst.setHasPromotion(git('PROMOTION_DWARF'), True)
						if bBronze == True:
							newUnitFirst.setHasPromotion(git('PROMOTION_BRONZE_WEAPONS'), True)
					elif bPoison == True and pType == 2:
						newUnitFirst.setHasPromotion(git('PROMOTION_POISONED_WEAPON'), True) # Poisoned Blade switched for Poisoned Weapon
				for j in xrange(iCount2):
					newUnitSecond = pPlayer2.initUnit(pUnitType2, pPlot2.getX(), pPlot2.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					if bPoison == True:
						newUnitSecond.setHasPromotion(git('PROMOTION_POISONED_BLADE'), True)

		elif iData1 == 109:
			iButtonId	= iData2
			iUnit		= iData3
			iPlayer		= iData4
			pPlayer		= gc.getPlayer(iPlayer)
			pUnit		= pPlayer.getUnit(iUnit)
			git			= gc.getInfoTypeForString
			if iButtonId == 0:
				possibleGoodies = []
				iRnd = CyGame().getSorenRandNum(2, "Lair Depth, Roll Class")
				if iRnd == 0:
					eGoodyClass = git("GOODYCLASS_GENERIC_MODERATE")
				else:
					eGoodyClass = git("GOODYCLASS_GENERIC_MAJOR")
				for i in xrange(gc.getNumGoodyInfos()):
					if gc.getGoodyInfo(i).isGoodyClassType(eGoodyClass):
						if (pPlayer.canReceiveGoody(pUnit.plot(), i, pUnit)):
							possibleGoodies.append(i)
				if possibleGoodies:
					eGoody = possibleGoodies[CyGame().getSorenRandNum(len(possibleGoodies), "Lair Depth, Roll Goody")]
					pPlayer.receiveGoody(pUnit.plot(), eGoody, pUnit)

		elif iData1 == 110:
			iButtonId	= iData2
			iPlayer		= iData3
			pPlayer		= gc.getPlayer(iPlayer)
			iChange = 0
			if iButtonId == 2:
				return
			if iButtonId == 0:
				iChange	= -5
			if iButtonId == 1:
				iChange = 5
			pPlayer.changeGlobalCounterContrib(iChange)
			CyGame().changeGlobalCounter(iChange)

		elif iData1 == 111:
			iButtonId	= iData2
			iPlayer		= iData3
			pPlayer		= gc.getPlayer(iPlayer)
			git			= gc.getInfoTypeForString
			bOption2	= False
			pCapital	= pPlayer.getCapitalCity()
			lReqBonus = [git("BONUS_COW"),git("BONUS_DEER"),git("BONUS_PIG"),git("BONUS_DEER_ARCTIC"),git("BONUS_BANANA"),git("BONUS_RICE"),git("BONUS_WHEAT"),git("BONUS_WINE"),git("BONUS_CORN")]
			for i in range (CyMap().numPlots()):
				iPlot = CyMap().plotByIndex(i)
				if iPlot.getBonusType(-1) in lReqBonus and iPlot.getOwner() == iPlayer:
					bOption2 = True
			if pPlayer.getGold() < 350 and iButtonId >= 0: # I don't know how else to simulate option shift caused by reqs in popup
				iButtonId += 1
			if bOption2 != True and iButtonId >= 1: # Option shift
				iButtonId += 1
			if pPlayer.getCivilizationType() != git("CIVILIZATION_KURIOTATES") or pCapital == -1 or pCapital.isNone(): # Option shift
				if iButtonId >= 2:
					iButtonId += 1
			if iButtonId == 3:
				return
			if iButtonId == 0:
				pPlayer.changeGold(-350)
			if iButtonId == 1:
				iRemovedBonus = 0
				for i in range (CyMap().numPlots()):
					if iRemovedBonus == 0:
						iPlot = CyMap().plotByIndex(i)
						if iPlot.getBonusType(-1) in lReqBonus and iPlot.getOwner() == iPlayer:
							iPlot.setBonusType(-1)
							iRemovedBonus += 1
			if iButtonId == 2:
				pCapital = pPlayer.getCapitalCity()
				pCapital.changePopulation(1)
			pPlayer.setHasFlag(git('FLAG_DEAL_WITH_CENTAURS_TRIBE'), True)
			# TODO Remove comment when setFreePromotion is exposed to python
			# pPlayer.setFreePromotion(git("UNITCOMBAT_MOUNTED"),git("PROMOTION_SHOCK"),true)

		elif iData1 == 112:
			iButtonId	= iData2
			iPlayer		= iData3
			iUnit		= iData4
			pPlayer		= gc.getPlayer(iPlayer)
			pUnit		= pPlayer.getUnit(iUnit)
			git			= gc.getInfoTypeForString
			pPlot		= pUnit.plot()
			if pPlayer.getCivilizationType() != git('CIVILIZATION_MAZATL') and pPlayer.getCivilizationType() !=  git('CIVILIZATION_CUALLI') and iButtonId >= 2: # I don't know how else to simulate option shift caused by reqs in popup
				iButtonId += 1
			if iButtonId == 3:
				return
			iGold = 250 + CyGame().getSorenRandNum(100, "CityOfGold Gold")
			if iButtonId == 2:
				pPlayer.changeGoldenAgeTurns(CyGame().goldenAgeLength())
				pPlayer.changeGold(iGold)
				return
			if iButtonId == 0:
				pPlayer.changeGold(iGold)
			iRnd = CyGame().getSorenRandNum(100, "CityOfGold Guards")
			if iButtonId == 1 or iRnd < 34: # Spawn Guards
				pOrcPlayer	= gc.getPlayer(gc.getORC_PLAYER())
				pNewPlot	= findClearPlot(-1, pPlot)
				newUnit1		= pOrcPlayer.initUnit(git('UNIT_LIZARD_PRIEST_OF_AGRUONN'), pNewPlot.getX(), pNewPlot.getY(), UnitAITypes.UNITAI_EXPLORE, DirectionTypes.DIRECTION_SOUTH)
				newUnit1.setHasPromotion(git('PROMOTION_COMBAT1'),True)
				newUnit1.setHasPromotion(git('PROMOTION_COMBAT2'),True)
				newUnit2		= pOrcPlayer.initUnit(git('UNIT_LIZARD_BLOWPIPE'), pNewPlot.getX(), pNewPlot.getY(), UnitAITypes.UNITAI_EXPLORE, DirectionTypes.DIRECTION_SOUTH)
				newUnit2.setHasPromotion(git('PROMOTION_COMBAT1'),True)
				newUnit3		= pOrcPlayer.initUnit(git('UNIT_LIZARD_BLOWPIPE'), pNewPlot.getX(), pNewPlot.getY(), UnitAITypes.UNITAI_EXPLORE, DirectionTypes.DIRECTION_SOUTH)
				newUnit3.setHasPromotion(git('PROMOTION_COMBAT1'),True)
				if iButtonId == 1:
					pUnit.changeImmobileTimer(3)
					pUnit.setHasPromotion(git('PROMOTION_PILLAGED_GOLD'),True)

		elif iData1 == 113:
			iButtonId		= iData2
			iData1			= iData3
			iData2			= iData4
			gc				= CyGlobalContext()
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iData2)
			pCaster			= pPlayer.getUnit(iData1)
			pPlot			= pCaster.plot()
			iPlayer			= gc.getGame().getActivePlayer()
			listCommander	= []
			pCommander		= -1
			for i in range(pPlot.getNumUnits()): # forming the list identical to findCommanderHuman
				pUnit = pPlot.getUnit(i)
				if pUnit.getOwner() == pCaster.getOwner():
					if not pUnit.getID() == pCaster.getID():	
						if pCaster.getDomainType() == pUnit.getDomainType():
							bvalid=True
							pLoopCommander=pUnit.getCommanderUnit()
							while( not pLoopCommander.isNone()):
								if (pLoopCommander.getID()==pCaster.getID()):
									bvalid=False
									break
								pLoopCommander=pLoopCommander.getCommanderUnit()
							if (not bvalid):
								continue
							if not pUnit.getID() == pCaster.getCommanderUnit().getID() and not pUnit.getCommanderUnit().getID() == pCaster.getID():
								if pUnit.getNumMinions() < pUnit.getCommandLimit():
									if pCaster.getUnitClassType() == git("UNITCLASS_SLUGA") or pCaster.getUnitClassType() == git("UNITCLASS_BATTLE_SLUGA") or pCaster.getUnitClassType() == git("UNITCLASS_WAR_SLUGA") or pCaster.getUnitClassType() == git("UNITCLASS_BEHEMOTH_SLUGA"):
										if pUnit.getUnitClassType() == git("UNITCLASS_OVERSEER") or pUnit.getUnitClassType() == git("UNITCLASS_COMBAT_OVERSEER") or pUnit.getUnitClassType() == git("UNITCLASS_SLUGA_COMMANDER") or pUnit.getUnitClassType() == git("UNITCLASS_KARAS"):
											listCommander.append(pUnit)
									else:
										iMinionRank = 0
										if pCaster.isHasPromotion(git('PROMOTION_GENERAL')):
											iMinionRank = 5
										elif pCaster.isHasPromotion(git('PROMOTION_CAPTAIN')):
											iMinionRank = 4
										elif pCaster.isHasPromotion(git('PROMOTION_MASTER_SEARGENT')):
											iMinionRank = 3
										elif pCaster.isHasPromotion(git('PROMOTION_SEARGENT')):
											iMinionRank = 2
										elif pCaster.isHasPromotion(git('PROMOTION_CORPORAL')):
											iMinionRank = 1
										elif pCaster.getCommandLimit() > 0:
											iMinionRank = 6
										iCommanderRank = 6
										if pUnit.isHasPromotion(git('PROMOTION_GENERAL')):
											iCommanderRank = 5
										elif pUnit.isHasPromotion(git('PROMOTION_CAPTAIN')):
											iCommanderRank = 4
										elif pUnit.isHasPromotion(git('PROMOTION_MASTER_SEARGENT')):
											iCommanderRank = 3
										elif pUnit.isHasPromotion(git('PROMOTION_SEARGENT')):
											iCommanderRank = 2
										elif pUnit.isHasPromotion(git('PROMOTION_CORPORAL')):
											iCommanderRank = 1
										if iCommanderRank > iMinionRank:
											listCommander.append(pUnit)
			if iButtonId != 0:
				pCommander = listCommander[iButtonId-1] # First button is used to cancel action
			if pCommander != -1:
				pCommander.addMinion(pCaster)
				pCaster.DeselectUnit()
				pCaster.SelectUnit()

		elif iData1 == 114:
			iButtonId		= iData2
			iPlayer			= iData3
			gc				= CyGlobalContext()
			pPlayer			= gc.getPlayer(iPlayer)
			git				= gc.getInfoTypeForString
			lTribeLeaders	= [git("LEADER_SHIMASANI"),git("LEADER_SOYALA"),git("LEADER_MOTSQUEH"),git("LEADER_OSYKA"),git("LEADER_ALOSAKA")]
			lLeaderText		= ["TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_SHIMASANI_WINS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_SOYALA_WINS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_MOTSQUEH_WINS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_OSYKA_WINS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_ALOSAKA_WINS"]
			lAltPassText	= ["TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_SHIMASANI_WINS_ALREADY_SHIMASANI_SUCCESS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_SOYALA_WINS_ALREADY_SOYALA_SUCCESS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_MOTSQUEH_WINS_ALREADY_MOTSQUEH_SUCCESS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_OSYKA_WINS_ALREADY_OSYKA_SUCCESS","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_ALOSAKA_WINS_ALREADY_ALOSAKA_SUCCESS"]
			lAltFailText	= ["TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_SHIMASANI_WINS_ALREADY_SHIMASANI_FAIL","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_SOYALA_WINS_ALREADY_SOYALA_FAIL","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_MOTSQUEH_WINS_ALREADY_MOTSQUEH_FAIL","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_OSYKA_WINS_ALREADY_OSYKA_FAIL","TXT_KEY_EVENT_TRIBAL_LAW_ELECTION_ALOSAKA_WINS_ALREADY_ALOSAKA_FAIL"]
			bAnarchy		= True
			iLeader			= iButtonId
			iRnd			= CyGame().getSorenRandNum(100, "TribalLaw, Bonus")
			if iButtonId == 5:										# Fair, No Anarchy, Happy city timer
				bAnarchy = False
				iHappyTurns = 1
				pPlayer.changeCivCounter(1)
				if pPlayer.getCivCounter() == 3:
					pPlayer.setCivCounter(0)
					iHappyTurns = 6
				(loopCity, iter) = pPlayer.firstCity(False)
				while(loopCity):
					loopCity.changeHappinessTimer(iHappyTurns)
					(loopCity, iter) = pPlayer.nextCity(iter, False)
				iLeader = CyGame().getSorenRandNum(len(lTribeLeaders), "TribalLaw, Fair Pick")
			else:
				pPlayer.setCivCounter(0)
			if iButtonId == 6:										# No Elections
				pPlayer.changeAnarchyTurns(1)
				return
			if bAnarchy == True and iLeader != 0:					# Anarchy Check
				pPlayer.changeAnarchyTurns(1)
			if pPlayer.getLeaderType() != lTribeLeaders[iLeader]:	# Leader Change
				pPlayer.changeLeader(lTribeLeaders[iLeader])
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText(lLeaderText[iLeader], ()),'',3,'art/Modules/ChislevExpansion/Buttons/Tribal_Law_Button.dds',git("COLOR_GREEN"),pPlayer.getCapitalCity().getX(),pPlayer.getCapitalCity().getY(),True,True)
			elif iRnd < 50:											# Same Leader, Failed 50/50, no Bonus
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText(lAltFailText[iLeader], ()),'',3,'art/Modules/ChislevExpansion/Buttons/Tribal_Law_Button.dds',git("COLOR_RED"),pPlayer.getCapitalCity().getX(),pPlayer.getCapitalCity().getY(),True,True)
			elif iRnd >= 50:										# Same Leader, Passed 50/50, do Bonus
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText(lAltPassText[iLeader], ()),'',3,'art/Modules/ChislevExpansion/Buttons/Tribal_Law_Button.dds',git("COLOR_GREEN"),pPlayer.getCapitalCity().getX(),pPlayer.getCapitalCity().getY(),True,True)
				if iLeader == 0: # Eagle
					for iLoopPlayer in range(gc.getMAX_CIV_PLAYERS()):
						loopPlayer = gc.getPlayer(iLoopPlayer)
						if loopPlayer.isAlive():
							if loopPlayer.getTeam() != pPlayer.getTeam():
								loopPlayer.AI_changeAttitudeExtra(iPlayer, 3)
								pPlayer.AI_changeAttitudeExtra(iLoopPlayer, 3)
				elif iLeader == 1: # Coyote
					pPlayer.initUnit(git('UNIT_ARTIST'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				elif iLeader == 2: # Bear
					pPlayer.initUnit(git('UNIT_ENGINEER'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				elif iLeader == 3: # Serpent
					pPlayer.initUnit(git('UNIT_COMMANDER'), pPlayer.getCapitalCity().getX(), pPlayer.getCapitalCity().getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
				elif iLeader == 4: # Tortoise
					pPlayer.changeGoldenAgeTurns(CyGame().goldenAgeLength())

		elif iData1 == 115:
			iButtonId		= iData2
			iPlayer			= iData3
			pPlayer			= CyGlobalContext().getPlayer(iPlayer)
			lLeaders		= [CyGlobalContext().getInfoTypeForString("LEADER_CHISLEV"),CyGlobalContext().getInfoTypeForString("LEADER_NATANE")]
			pPlayer.changeLeader(lLeaders[iButtonId])

		elif iData1 == 116:
			iButtonId		= iData2
			iUnitID			= iData3
			iPlayer			= iData4
			pUnit			= CyGlobalContext().getPlayer(iPlayer).getUnit(iUnitID)
			git				= CyGlobalContext().getInfoTypeForString
			lPromotion1		= [git("PROMOTION_MENAWA_EAGLE_TRIBE"),git("PROMOTION_MENAWA_COYOTE_TRIBE"),git("PROMOTION_MENAWA_BEAR_TRIBE"),git("PROMOTION_MENAWA_SERPENT_TRIBE"),git("PROMOTION_MENAWA_TORTOISE_TRIBE")]
			lPromotion2		= [git("PROMOTION_MOBILITY1"),git("PROMOTION_DRILL1"),git("PROMOTION_COMBAT1"),git("PROMOTION_CITY_RAIDER1"),git("PROMOTION_CITY_GARRISON1")]
			lPromotion3		= [git("PROMOTION_MOBILITY2"),git("PROMOTION_DRILL2"),git("PROMOTION_COMBAT2"),git("PROMOTION_CITY_RAIDER2"),git("PROMOTION_CITY_GARRISON2")]
			pUnit.setHasPromotion(lPromotion1[iButtonId],True)
			if pUnit.isHasPromotion(lPromotion2[iButtonId]):
				pUnit.setHasPromotion(lPromotion3[iButtonId],True)
			pUnit.setHasPromotion(lPromotion2[iButtonId],True)

		elif iData1 == 117:
			iButtonId		= iData2
			iCaster			= iData3
			iPlayer			= iData4
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iPlayer)
			pCaster			= pPlayer.getUnit(iCaster)
			pPlot			= pCaster.plot()
			lSpell			= [[git("SPELL_SUMMON_FROSTLING_WARRIOR_GREATOR"),git("SPELL_SUMMON_FROSTLING_ARCHER_GREATOR")],[git("SPELL_SUMMON_WINTER_WOLF_GREATOR")],[git("SPELL_SUMMON_KOCRACHON_GREATOR")],[git("SPELL_SUMMON_ICE_ELEMENTAL_GREATOR")],[git("SPELL_SUMMON_AQUILAN_GREATOR")],[git("SPELL_SUMMON_FROST_GIANT_GREATER")]]
			for iSpell in lSpell[iButtonId]:
				pCaster.cast(iSpell)

		elif iData1 == 118:
			iButtonId		= iData2
			iUnit			= iData3
			iPlayer			= iData4
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iPlayer)
			pUnit			= pPlayer.getUnit(iUnit)
			if iButtonId == 1:
				return
			pUnit.setHasPromotion(git('PROMOTION_GELA'), False)
			CyGame().changeGlobalCounter(-10)
			pPlayer.changeGlobalCounterContrib(-10)
			newUnit = pPlayer.initUnit(git('UNIT_ANGEL'), pUnit.getX(), pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
			newUnit.setHasPromotion(git('PROMOTION_HERO'), True)
			CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_BASIUM_GELA",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Units/Basium.dds',ColorTypes(7),pUnit.getX(),pUnit.getY(),True,True)
			for iLoopPlayer in xrange(gc.getMAX_PLAYERS()):
				pLoopPlayer	= gc.getPlayer(iLoopPlayer)
				if pLoopPlayer.getCivilizationType() == git('CIVILIZATION_MERCURIANS'):
					pLoopPlayer.AI_changeAttitudeExtra(3,1)

		elif iData1 == 119:
			iButtonId		= iData2
			iUnit			= iData3
			iPlayer			= iData4
			iImprovement	= iData5
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iPlayer)
			pUnit			= pPlayer.getUnit(iUnit)
			pPlot			= pUnit.plot()
			if iButtonId == 1:
				return
			if iImprovement == git("IMPROVEMENT_BROKEN_SEPULCHER"):
				pUnit.setHasPromotion(git('PROMOTION_GELA'), False)
				for pyCity in PyPlayer(iPlayer).getCityList() :
					pCity = pyCity.GetCy()
					if CyGame().getSorenRandNum(100,"effect Gela, Broken Sepulcher") <= 60:
						newUnit = pPlayer.initUnit(git('UNIT_MANES'), pCity.getX(), pCity.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					if pCity.getPopulation() > 2:
						pCity.changePopulation(-2)
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_GELA_BROKEN",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/brokensepulcher.dds',ColorTypes(7),pUnit.getX(),pUnit.getY(),True,True)
			elif iImprovement == git("IMPROVEMENT_MIRROR_OF_HEAVEN"):
				pUnit.setHasPromotion(git('PROMOTION_GELA'), False)
				pUnit.setHasPromotion(git('PROMOTION_TEMP_HELD'), True)
				pUnit.setHasPromotion(git('PROMOTION_SOL'), True)
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_GELA_MIRROR",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/mirrorofheaven.dds',ColorTypes(7),pUnit.getX(),pUnit.getY(),True,True)
				pDemonPlayer = gc.getPlayer(gc.getDEMON_PLAYER())
				for iPlayer2 in range(gc.getMAX_PLAYERS()):
					pPlayer2 = gc.getPlayer(iPlayer2)
					if (pPlayer2.isAlive()):
						if pPlayer2.getCivilizationType() == git('CIVILIZATION_INFERNAL'):
							pDemonPlayer = pPlayer2
							enemyTeam = pDemonPlayer.getTeam()
							pTeam = gc.getTeam(pPlayer.getTeam())
							pTeam.declareWar(enemyTeam, true, WarPlanTypes.WARPLAN_TOTAL)
				for iiX in range(pUnit.getX()-2, pUnit.getX()+3, 1):
					for iiY in range(pUnit.getY()-2, pUnit.getY()+3, 1):
						pPlot2 = CyMap().plot(iiX,iiY)
						if not pPlot2.isWater() and not pPlot2.isCity() and pPlot2.getNumUnits() == 0 and pPlot2.isFlatlands():
							if CyGame().getSorenRandNum(500, "effect Gela, Hellfire") <= 400:
								iImprovement = pPlot2.getImprovementType()
								bValid = True
								if iImprovement != -1 :
									if gc.getImprovementInfo(iImprovement).isPermanent():
										bValid = False
								if bValid :
									pPlot2.setImprovementType(git('IMPROVEMENT_HELLFIRE'))
									newUnit = pDemonPlayer.initUnit(git('UNIT_SECT_OF_FLIES'), pPlot2.getX(), pPlot2.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
									newUnit.setHasPromotion(git('PROMOTION_DEMON'), True)
			elif iImprovement == git("IMPROVEMENT_POOL_OF_TEARS"):
				pUnit.setHasPromotion(git('PROMOTION_GELA'), False)
				pUnit.setHasPromotion(git('PROMOTION_PIKE_OF_TEARS'), True)
				CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_TEARS_GELA",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/pooloftears.dds',ColorTypes(8),pUnit.getX(),pUnit.getY(),True,True)
				iRnd = CyGame().getSorenRandNum(100, "effect Gela, Pool of Tears, Plague") <= 20
				if iRnd <= 20 or (pPlayer.getStateReligion() != git('RELIGION_FELLOWSHIP_OF_LEAVES') and iRnd <= 50):
					CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_TEARS_GELA_PLAGUE",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/pooloftears.dds',ColorTypes(8),pUnit.getX(),pUnit.getY(),True,True)
					for iPlayer2 in range(gc.getMAX_PLAYERS()):
						pPlayer2 = gc.getPlayer(iPlayer2)
						if pPlayer2.getCivilizationType() != git('CIVILIZATION_INFERNAL'):
							for pyCity in PyPlayer(iPlayer2).getCityList() :
								pCity = pyCity.GetCy()
								i = CyGame().getSorenRandNum(5, "Blight")
								i += pCity.getPopulation() - 2
								i -= pCity.totalGoodBuildingHealth()
								pCity.changeEspionageHealthCounter(i)
								py = PyPlayer(iPlayer2)
								for pUnit2 in py.getUnitList():
									if pUnit2.isAlive():
										pUnit2.doDamageNoCaster(10, 100, git('DAMAGE_DEATH'), false)
			elif iImprovement == git("IMPROVEMENT_PYRE_OF_THE_SERAPHIC"):
				pUnit.setHasPromotion(git('PROMOTION_GELA'), False)
				pPlot.setImprovementType(-1)
				if CyGame().getSorenRandNum(100,"effect Gela, Pyre") <= 40:
					pUnit.setHasPromotion(git('PROMOTION_FROZEN_FLAME'), True)
					CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_TEARS_GELA_PYRE_1",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/pyreoftheseraphic.dds',ColorTypes(8),pUnit.getX(),pUnit.getY(),True,True)
				else:
					mapSize = CyMap().getWorldSize()
					# i from 1 (duel) to 9 (huger)
					i = 1 + mapSize + int(mapSize/5) + int(mapSize/6)
					addBonus('BONUS_MANA',i,'Art/Interface/Buttons/WorldBuilder/mana_button.dds')
					CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_TEARS_GELA_PYRE_2",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/pyreoftheseraphic.dds',ColorTypes(8),pUnit.getX(),pUnit.getY(),True,True)
			elif iImprovement == git("IMPROVEMENT_MAELSTROM"):
				pUnit.setHasPromotion(git('PROMOTION_GELA'), False)
				pUnit.kill(True, PlayerTypes.NO_PLAYER)
				if  pPlayer.getStateReligion() == git('RELIGION_OCTOPUS_OVERLORDS'):
					newUnit1 = pPlayer.initUnit(git('UNIT_STYGIAN_GUARD'), pUnit.getX()+1, pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					newUnit1.setHasPromotion(git('PROMOTION_WATER_WALKING'), True)
					newUnit2 = pPlayer.initUnit(git('UNIT_STYGIAN_GUARD'), pUnit.getX()+1, pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					newUnit2.setHasPromotion(git('PROMOTION_WATER_WALKING'), True)
					newUnit3 = pPlayer.initUnit(git('UNIT_STYGIAN_GUARD'), pUnit.getX()+1, pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					newUnit3.setHasPromotion(git('PROMOTION_WATER_WALKING'), True)
					newUnit4 = pPlayer.initUnit(git('UNIT_STYGIAN_GUARD'), pUnit.getX()+1, pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					newUnit4.setHasPromotion(git('PROMOTION_WATER_WALKING'), True)
					newUnit5 = pPlayer.initUnit(git('UNIT_DISCIPLE_OCTOPUS_OVERLORDS'), pUnit.getX()+1, pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					newUnit5.setHasPromotion(git('PROMOTION_WATER_WALKING'), True)
					newUnit5.setHasPromotion(git('PROMOTION_HERO'), True)
					CyInterface().addMessage(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_MAELSTROM_GELA_1",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/Maelstrom.dds',ColorTypes(7),pUnit.getX(),pUnit.getY(),True,True)
				else:
					iStygianChance = 300
					pDemonPlayer = gc.getPlayer(gc.getDEMON_PLAYER())
					for i in range (CyMap().numPlots()):
						pPlot = CyMap().plotByIndex(i)
						if pPlot.isWater() and pPlot.getNumUnits() == 0:
							if CyGame().getSorenRandNum(10000, "effect Gela, Stygian") <= iStygianChance:
								newUnit = pDemonPlayer.initUnit(git('UNIT_STYGIAN_GUARD'), pPlot.getX(), pPlot.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
								newUnit.setUnitAIType(git('UNITAI_ANIMAL'))
								newUnit.setHasPromotion(git('PROMOTION_WATER_WALKING'), True)
							elif CyGame().getSorenRandNum(10000, "effect Gela, SeaSerpent") <= iStygianChance:
								newUnit = pDemonPlayer.initUnit(git('UNIT_SEA_SERPENT'), pPlot.getX(), pPlot.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
								newUnit.setUnitAIType(git('UNITAI_ANIMAL'))
								newUnit.setHasPromotion(git('PROMOTION_WATER_WALKING'), True)
					CyInterface().addMessage(pUnit.getOwner(),True,25,CyTranslator().getText("TXT_KEY_MESSAGE_MAELSTROM_GELA_2",()),'AS2D_FEATUREGROWTH',3,'Art/Interface/Buttons/Improvements/Maelstrom.dds',ColorTypes(7),pUnit.getX(),pUnit.getY(),True,True)

		elif iData1 == 120:
			iButtonId		= iData2
			iPlayer			= iData3
			iUnit			= iData4
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iPlayer)
			pUnit			= pPlayer.getUnit(iUnit)
			pPlot			= pUnit.plot()
			iRnd			= CyGame().getSorenRandNum(100,"OrphanedGoblin effect")
			if iButtonId == 0:
				pUnit.setHasPromotion(git('PROMOTION_ORC_SLAYING'), True)
				pUnit.setHasPromotion(git('PROMOTION_CRAZED'), True)
			elif iButtonId == 1:
				pUnit.setHasPromotion(git('PROMOTION_GOBLIN'), True)
			elif iButtonId == 2:
				pNewPlot = findClearPlot(-1, pPlot)
				if pNewPlot != -1:
					if iRnd < 50:
						pGoblinPlayer = gc.getPlayer(gc.getORC_PLAYER())
					else:
						pGoblinPlayer = pPlayer
					newUnit = pGoblinPlayer.initUnit(git('UNIT_GOBLIN'), pNewPlot.getX(),pNewPlot.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
					newUnit.setHasPromotion(git('PROMOTION_WEAK'), True)
			else:
				pUnit.changeExperience(-1,-1,False,False,False)
				newUnit = pPlayer.initUnit(git('UNIT_GOBLIN'), pPlot.getX(),pPlot.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)

		elif iData1 == 121:
			gc = CyGlobalContext()
			val_answer = iData2
			iCity = iData3
			iOwner = iData4
			pPlayer = gc.getPlayer(iOwner)
			pCity = pPlayer.getCity(iCity)
			pPlot = pCity.plot()
			if val_answer == 0:
				pPlot.setBonusType(gc.getInfoTypeForString('BONUS_NIGHTMARE'))
			if val_answer == 1:
				pPlot.setBonusType(gc.getInfoTypeForString('BONUS_ASH'))

		elif iData1 == 122:
			gc = CyGlobalContext()
			val_answer = iData2
			iCity = iData3
			iOwner = iData4
			pPlayer = gc.getPlayer(iOwner)
			if val_answer == 1:
				pCity = pPlayer.getCity(iCity)
				pPlot = pCity.plot()
				pPlot.setBonusType(gc.getInfoTypeForString('BONUS_ASH'))

		elif iData1 == 123: # Take Equipment
			iButtonId		= iData2
			iCaster			= iData3
			iPlayer			= iData4
			cf				= CustomFunctions.CustomFunctions()
			pPlayer			= gc.getPlayer(iPlayer)
			pCaster			= pPlayer.getUnit(iCaster)
			pPlot			= pCaster.plot()
			lEquipmentList	= []
			if iButtonId == 0:	# Cancel
				return
			for iUnit in xrange(pPlot.getNumUnits()):
				pUnit = pPlot.getUnit(iUnit)
				if pUnit.isCommunalProperty():
					for iPromotion in xrange(gc.getNumPromotionInfos()):
						if pUnit.isHasPromotion(iPromotion) and gc.getPromotionInfo(iPromotion).isEquipment():
							if not pCaster.isHasPromotion(iPromotion):
								if not iPromotion in lEquipmentList:
									if cf.canRemoveEquipment(-1,pCaster,iPromotion) == True:
										lEquipmentList.append(iPromotion)
			iEquipment		= lEquipmentList[iButtonId - 1] 
			for iUnit in xrange(pPlot.getNumUnits()):
				pUnit = pPlot.getUnit(iUnit)
				if pUnit.isCommunalProperty() and pUnit.isHasPromotion(iEquipment):
					pUnit.setHasPromotion(iEquipment, False)
					pCaster.setHasPromotion(iEquipment, True)

		elif iData1 == 124: # Drop Equipment
			iButtonId		= iData2
			iCaster			= iData3
			iPlayer			= iData4
			cf				= CustomFunctions.CustomFunctions()
			git				= gc.getInfoTypeForString
			pPlayer			= gc.getPlayer(iPlayer)
			pCaster			= pPlayer.getUnit(iCaster)
			pPlot			= pCaster.plot()
			lEquipmentList	= []
			containerUnit = -1
			if iButtonId == 0: # Cancel
				return
			for iUnit in xrange(pPlot.getNumUnits()):
				if pPlot.getUnit(iUnit).getUnitType() == git('EQUIPMENT_CONTAINER'):
					containerUnit = pPlot.getUnit(iUnit)
			if containerUnit == -1:
				containerUnit = gc.getPlayer(gc.getORC_PLAYER()).initUnit(git('EQUIPMENT_CONTAINER'), pPlot.getX(), pPlot.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
			for iPromotion in xrange(gc.getNumPromotionInfos()):
				if pCaster.isHasPromotion(iPromotion) and gc.getPromotionInfo(iPromotion).isEquipment():
					if cf.canRemoveEquipment(pCaster,-1,iPromotion) == True:
						lEquipmentList.append(iPromotion)
			if iButtonId == 1: # All
				for iPromotion in lEquipmentList:
					containerUnit.setHasPromotion(iPromotion,True)
					pCaster.setHasPromotion(iPromotion,False)
			elif iButtonId > 1:
				containerUnit.setHasPromotion(lEquipmentList[iButtonId - 2],True)
				pCaster.setHasPromotion(lEquipmentList[iButtonId - 2],False)

		elif iData1 == 125: # Swap Equipment
			iButtonId		= iData2
			iCaster			= iData3
			iPlayer			= iData4
			cf				= CustomFunctions.CustomFunctions()
			pPlayer			= gc.getPlayer(iPlayer)
			pCaster			= pPlayer.getUnit(iCaster)
			pPlot			= pCaster.plot()
			lEquipmentUnitPairs = []
			if iButtonId == 0: # Cancel
				return
			for iUnit in xrange(pPlot.getNumUnits()):
				pUnit = pPlot.getUnit(iUnit)
				if not pUnit.isCommunalProperty() and pUnit.getOwner() == iPlayer:
					for iPromotion in xrange(gc.getNumPromotionInfos()):
						if pUnit.isHasPromotion(iPromotion) and gc.getPromotionInfo(iPromotion).isEquipment():
							if not pCaster.isHasPromotion(iPromotion):
								if cf.canRemoveEquipment(pUnit,pCaster,iPromotion) == True:
									lPair = [iPromotion,pUnit]
									lEquipmentUnitPairs.append(lPair)
			lPair		= lEquipmentUnitPairs[iButtonId - 1]
			iPromotion	= lPair[0]
			pHolder		= lPair[1]
			pCaster.setHasPromotion(iPromotion,True)
			pHolder.setHasPromotion(iPromotion,False)

		elif iData1 == 20 : # Goblin CityClass Choice iData1=20, iData2=CityID, iData3=CityClassId, iData4=PlayerId
			pPlayer = gc.getPlayer(iData4)
			pCity = pPlayer.getCity(iData2)
			pCity.setCityClass(iData3)
		elif iData1 == 21 : # Kurio Settlement choice iData1=21, iData2=CityID, iData3 = 1(True) or 0(False) , iData4=PlayerId
			pPlayer = gc.getPlayer(iData4)
			pCity = pPlayer.getCity(iData2)
			if(iData3==1):
				pCity.setSettlement(True)
			else:
				pCity.setSettlement(False)
		elif iData1==22 : # Important Trait choice  iData1=22 , iData2=TraitId, iData3= 1(True) or 0(False), iData4=PlayerId
			pPlayer = gc.getPlayer(iData4)
			if (iData3==1):
				pPlayer.setHasTrait(iData2,True)
				pPlayer.initValidTraitTriggers()
				pPlayer.setGainingTrait(False)
			else:
				pPlayer.setTraitPoints(iData2,0)
				pPlayer.setGainingTrait(False)
		## *******************
		## Modular Python: ANW 29-may-2010
		for module in command['onModNetMessage']:
			module.onModNetMessage(self, argsList)

		## Modular Python End
		## *******************

	def onInit(self, argsList):
		'Called when Civ starts up'
		CvUtil.pyPrint( 'OnInit' )

		## *******************
		## Modular Python: ANW 29-may-2010

		self.pluginScan()

		## Modular Python End
		## *******************

	def onUpdate(self, argsList):
		'Called every frame'
		fDeltaTime = argsList[0]

		# allow camera to be updated
		CvCameraControls.g_CameraControls.onUpdate( fDeltaTime )

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUpdate']:
			module.onUpdate(self, argsList)

		## Modular Python End
		## *******************

	def onWindowActivation(self, argsList):
		'Called when the game window activates or deactivates'
		bActive = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onWindowActivation']:
			module.onWindowActivation(self, argsList)

		## Modular Python End
		## *******************

	def onUnInit(self, argsList):
		'Called when Civ shuts down'
		CvUtil.pyPrint('OnUnInit')

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnInit']:
			module.onUnInit(self, argsList)

		## Modular Python End
		## *******************

	def onPreSave(self, argsList):
		"called before a game is actually saved"
		CvUtil.pyPrint('OnPreSave')

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onPreSave']:
			module.onPreSave(self, argsList)

		## Modular Python End
		## *******************

		if self.DbgWnd != None:
			CyGame().setScriptData(pickle.dumps(self.DbgWnd.saveData()))

	def onSaveGame(self, argsList):
		"return the string to be saved - Must be a string"

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onSaveGame']:
			module.onSaveGame(self, argsList)

		## Modular Python End
		## *******************

		return ""

	def verifyLoaded(self, bLoad = False):
		if self.LoadedData == False:
			self.loadData(bLoad)

	def loadData(self, bLoad = False):
		' Loading data and initializing variables '
		self.Tools 			= FoxTools.FoxTools()
		self.Tools.initialize()

		self.Defines		= self.Tools.getDefineDict()
		self.Eras 			= self.Tools.getEraDict()
		self.Techs			= self.Tools.getTechDict()
		self.Victories		= self.Tools.getVictoryDict()
		self.GameSpeeds 	= self.Tools.getGameSpeedDict()
		self.GameOptions 	= self.Tools.getGameOptionDict()
		self.EventTriggers	= self.Tools.getEventTriggerDict()

		self.Civilizations 	= self.Tools.getCivilizationDict()
		self.Leaders 		= self.Tools.getLeaderDict()
		self.LeaderStatus	= self.Tools.getLeaderStatusDict()
		self.Traits 		= self.Tools.getTraitDict()
		self.Civics 		= self.Tools.getCivicDict()
		self.Religions 		= self.Tools.getReligionDict()
		self.Corporations	= self.Tools.getCorporationDict()
		self.Alignments		= self.Tools.getAlignmentDict()

		self.Projects 		= self.Tools.getProjectDict()
		self.Buildings 		= self.Tools.getBuildingDict()
		self.Specialists	= self.Tools.getSpecialistDict()
		self.BuildingClasses= self.Tools.getBuildingClassDict()
		self.Processes		= self.Tools.getProcessesDict()

		self.Resources 		= self.Tools.getResourcesDict()
		self.WorldSizes 	= self.Tools.getWorldSizesDict()
		self.Terrain 		= self.Tools.getTerrainDict()
		self.Feature 		= self.Tools.getFeatureDict()
		self.Mana	 		= self.Tools.getManaDict()
		self.Goodies 		= self.Tools.getGoodyDict()

		self.Builds				= self.Tools.getBuildDict()
		self.Lairs 				= self.Tools.getLairDict()
		self.ManaNodes 			= self.Tools.getManaNodeDict()
		self.Improvements 		= self.Tools.getImprovementDict()
		self.CivImprovements 	= self.Tools.getCivImprovementDict()
		self.UniqueImprovements	= self.Tools.getUniqueImprovementDict()

		self.Units 			= self.Tools.getUnitDict()
		self.Heroes			= self.Tools.getHeroesDict()
		self.UnitAI			= self.Tools.getUnitAIDict()
		self.UnitClasses 	= self.Tools.getUnitClassDict()
		self.UnitCombats 	= self.Tools.getUnitCombatDict()
		self.GreatPeople 	= self.Tools.getGreatPeopleDict()
		self.Promotions 	= self.Tools.getPromotionDict()
		self.DamageTypes 	= self.Tools.getDamageTypesDict()

		self.cf				= CustomFunctions.CustomFunctions()
		self.cf.initialize()

		if bLoad:
			if FoxGlobals["USE_DEBUG_WINDOW"]:
				self.DbgWnd 		= FoxDebug.FoxDebug()
				self.DbgWnd.loadData(pickle.loads(CyGame().getScriptData()))

		self.LoadedData = True

	def onLoadGame(self, argsList):
		CvAdvisorUtils.resetNoLiberateCities()
		self.verifyLoaded(True)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onLoadGame']:
			module.onLoadGame(self, argsList)

		## Modular Python End
		## *******************

		return 0

	def onGameStart(self, argsList):
		'Called at the start of the game'

		# Loading Debug data and Initializing dictionaries
		self.verifyLoaded()

		gc = CyGlobalContext()
		cf				= self.cf
		getInfoType		= gc.getInfoTypeForString
		game 			= CyGame()
		map 			= CyMap()
		Option			= self.GameOptions
		getPlayer 		= gc.getPlayer
		plotByIndex 	= map.plotByIndex
		iNumPlots 		= map.numPlots()
		randNum 		= game.getSorenRandNum
		iMaxPlayers		= gc.getMAX_PLAYERS()
		iNoAI			= UnitAITypes.NO_UNITAI
		iSouth 			= DirectionTypes.DIRECTION_SOUTH
		
		if game.getWBMapScript():
			sf.gameStart()
		else:
			introMovie = CvIntroMovieScreen.CvIntroMovieScreen()
			introMovie.interfaceScreen()
		Animal		= self.Units["Animal"]
		
		
		gc.getGame().setGlobalFlag(gc.getInfoTypeForString('FLAG_AKHARIEN_LOST'),True)
		gc.getGame().setGlobalFlag(gc.getInfoTypeForString('FLAG_MOKKA_LOST'),True)
		
		if gc.getGame().isOption(GameOptionTypes.GAMEOPTION_BARBARIAN_WORLD):
			cf.doBarbarianWorld()
		#Wild Mana
		if gc.getGame().isOption(GameOptionTypes.GAMEOPTION_WILD_MANA):

			# Units
			Summon 			= self.Units["Summons"]
			Kahdi			= self.Units["Kahdi"]
			Mercurian		= self.Units["Mercurian"]
			Elohim			= self.Units["Elohim"]
			Grigori			= self.Units["Grigori"]
			Luchu			= self.Units["Luchuirp"]
			Sheaim			= self.Units["Sheaim"]
			Promo	 		= self.Promotions["Effects"]

			# Mana
			Mana 			= self.Mana

			bOrcPlayer 		= getPlayer(gc.getORC_PLAYER())
			bAnimalPlayer 	= getPlayer(gc.getANIMAL_PLAYER())
			bDemonPlayer 	= getPlayer(gc.getDEMON_PLAYER())
			demonInit		= bDemonPlayer.initUnit
			animalInit		= bAnimalPlayer.initUnit
			orcInit			= bOrcPlayer.initUnit

			
			lList = ['BONUS_MANA_SUN', 'BONUS_MANA_ICE', 'BONUS_MANA_AIR', 'BONUS_MANA_BODY', 'BONUS_MANA_CHAOS', 'BONUS_MANA_DEATH', 'BONUS_MANA_EARTH', 'BONUS_MANA_ENCHANTMENT', 'BONUS_MANA_ENTROPY', 'BONUS_MANA_FIRE', 'BONUS_MANA_LAW', 'BONUS_MANA_LIFE', 'BONUS_MANA_METAMAGIC', 'BONUS_MANA_MIND', 'BONUS_MANA_NATURE', 'BONUS_MANA_SHADOW', 'BONUS_MANA_SPIRIT', 'BONUS_MANA_WATER', 'BONUS_MANA_CREATION', 'BONUS_MANA_FORCE', 'BONUS_MANA_DIMENSIONAL', 'BONUS_MANA']

			#Initializing iMana, modified by World Size
			iMana = 15
			worldSize = map.getWorldSize()
			if worldSize 	== getInfoType("WORLDSIZE_DUEL"): 	iMana = iMana - 7;
			elif worldSize 	== getInfoType("WORLDSIZE_TINY"): 	iMana = iMana - 5;
			elif worldSize 	== getInfoType("WORLDSIZE_SMALL"):	iMana = iMana - 3;
			elif worldSize 	== getInfoType("WORLDSIZE_LARGE"):	iMana = iMana + 3;
			elif worldSize 	== getInfoType("WORLDSIZE_HUGE"):	iMana = iMana + 6;
			elif worldSize 	== getInfoType("WORLDSIZE_HUGER"):	iMana = iMana + 12;
			iMana=(int)(iMana)
			addBonus('BONUS_MANA',iMana,-1)

			iConvertRnd = 60
			if Option["Feral Mana"]:
				iConvertRnd = 100
			randNum = game.getSorenRandNum
			for i in xrange(map.numPlots()):
				pPlot = plotByIndex(i)
				if pPlot.getImprovementType() == -1:
					if not pPlot.isWater():
						iBonus = pPlot.getBonusType(-1)
						if iBonus == Mana["Mana"]:
							iManaRnd = randNum(100, "Mana Creation")
							if iManaRnd <= iConvertRnd:
								sMana = lList[randNum(len(lList), "Pick Mana")-1]
								iBonus = getInfoType(sMana)
								pPlot.setBonusType(iBonus)
								if Option["Mana Guardians"] and pPlot.getNumUnits()==0:
									iX = pPlot.getX(); iY = pPlot.getY();
									if iBonus == Mana["Air"] :
										newUnit = demonInit( Summon["Lightning Elemental"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Body"] :
										newUnit = demonInit( Summon["Flesh Golem"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Chaos"]:
										newUnit = demonInit( Sheaim["Chaos Marauder"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Death"]:
										newUnit = demonInit( Summon["Lich"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Held"], True)
									elif iBonus == Mana["Earth"]:
										newUnit = demonInit( Summon["Earth Elemental"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Enchantment"]:
										newUnit = orcInit( Luchu["Wood Golem"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Entropy"]:
										newUnit = demonInit( Sheaim["Tar Demon"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Fire"]:
										newUnit = demonInit( Summon["Fire Elemental"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Law"]:
										newUnit = orcInit( Summon["Einherjar"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Life"]:
										newUnit = orcInit( Mercurian["Angel"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Metamagic"]:
										newUnit = demonInit( Kahdi["Thade"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Mind"]:
										newUnit = demonInit( Kahdi["Psion"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Shadow"]:
										newUnit = demonInit( Summon["Spectre"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Spirit"]:
										newUnit = orcInit( Elohim["Monk"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Sun"]:
										newUnit = orcInit( Summon["Aurealis"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Water"]:
										newUnit = demonInit( Summon["Water Elemental"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Creation"]:
										newUnit = animalInit( Animal["Elk"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Force"]:
										newUnit = orcInit( Grigori["Dragon Slayer"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Dimensional"]:
										newUnit = demonInit( Kahdi["Uber Gnosling"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Ice"]:
										newUnit = demonInit( Summon["Ice Elemental"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
									elif iBonus == Mana["Nature"]:
										newUnit = animalInit( Summon["Guardian Vines"], iX, iY, iNoAI, iSouth)
										newUnit.setHasPromotion( Promo["Mana Guardian"], True)
			# END WILD MANA

		if Option["Thaw"]:

			Terrain			= self.Terrain
			Feature			= self.Feature

			# FlavourMod: Changed by Jean Elcard 11/06/2008 (Extended End of Winter Option)
			FLAT_WORLDS = ["ErebusWrap", "Erebus"]			# map scripts with wrapping but no equator
			MAX_EOW_PERCENTAGE = 0.35 						# percentage of EoW on total game turns
			THAW_DELAY_PERCENTAGE = 0.05 					# don't start thawing for x percent of EoW

			# forest varieties
			DECIDUOUS_FOREST = 0
			CONIFEROUS_FOREST = 1
			SNOWY_CONIFEROUS_FOREST = 2

			dice = game.getSorenRand()

			iTotalGameTurns = gc.getGameSpeedInfo(game.getGameSpeedType()).getGameTurnInfo(0).iNumGameTurnsPerIncrement
			iMaxEOWTurns = max(1, int(iTotalGameTurns * MAX_EOW_PERCENTAGE))
			iThawDelayTurns = max(1, int(iMaxEOWTurns * THAW_DELAY_PERCENTAGE))

			iMaxLatitude = max(map.getTopLatitude(), abs(map.getBottomLatitude()))
			bIsFlatWorld = not (map.isWrapX() or map.isWrapY()) or map.getMapScriptName() in FLAT_WORLDS

			getBonusInfo = gc.getBonusInfo
			for i in xrange(iNumPlots):
				pPlot 		= plotByIndex(i)
				eTerrain 	= pPlot.getTerrainType()
				eFeature 	= pPlot.getFeatureType()
				iVariety 	= pPlot.getFeatureVariety()
				eBonus 		= pPlot.getBonusType(TeamTypes.NO_TEAM)
				setTempT 	= pPlot.setTempTerrainTypeFM
				setTempF 	= pPlot.setTempFeatureType
				setTempB 	= pPlot.setTempBonusType

				iTurns = dice.get(iMaxEOWTurns - iThawDelayTurns, "End of Winter Thaw Requirement")
				if not bIsFlatWorld:
					iLatitude = abs(pPlot.getLatitude())
					iTurns = int(iTurns * ((float(iLatitude) / iMaxLatitude) ** 0.4))
				iTurns += iThawDelayTurns

				# cover erebus' oceans and lakes in ice
				if pPlot.isWater():
					if bIsFlatWorld:
						if dice.get(100, "End of Winter Iceburg Placement") < 90:
							setTempF(Feature["Ice"], 0, iTurns)
					elif iLatitude + 10 > dice.get(50, "End of Winter Glacier Placement"):
						setTempF(Feature["Ice"], 0, iTurns)

				# change terrains to colder climate versions
				if eTerrain == Terrain["Taiga"]:
					if dice.get(100, "Taiga to Tundra") < 90:
						setTempT(Terrain["Tundra"], iTurns, False, False)
				elif eTerrain == Terrain["Grass"]:
					if eFeature != Feature["Jungle"]:
						if dice.get(100, "Grass to Taiga or Tundra") < 60:
							setTempT(Terrain["Tundra"], iTurns, False, False)
						else:
							setTempT(Terrain["Taiga"], iTurns, False, False)
				elif eTerrain == Terrain["Plains"]:
					if dice.get(100, "Plains to Taiga or Tundra") < 30:
						setTempT(Terrain["Tundra"], iTurns, False, False)
					else:
						setTempT(Terrain["Taiga"], iTurns, False, False)
				elif eTerrain == Terrain["Desert"]:
					if dice.get(100, "Desert to Taiga or Plains") < 50:
						setTempT(Terrain["Taiga"], iTurns, False, False)
					else:
						setTempT(Terrain["Plains"], iTurns, False, False)
				elif eTerrain == Terrain["Marsh"]:
					setTempT(Terrain["Grass"], iTurns, False, False)

				# change all features (except ice) to colder climate versions
				if eFeature == Feature["Forest"]:
					if iVariety == DECIDUOUS_FOREST:
						setTempF(Feature["Forest"], CONIFEROUS_FOREST, iTurns)
					elif iVariety == CONIFEROUS_FOREST:
						setTempF(Feature["Forest"], SNOWY_CONIFEROUS_FOREST, iTurns)
				elif (eFeature != FeatureTypes.NO_FEATURE and not pPlot.isWater()):
					if eFeature != Feature["Ice"]:
						setTempF(Feature["Forest"], DECIDUOUS_FOREST, iTurns)
				elif (eFeature != FeatureTypes.NO_FEATURE and pPlot.isWater()):
					if eFeature != Feature["Ice"]:
						setTempF(Feature["Ice"], 0, iTurns)
						
				# remove invalid bonuses or replace them (if food) with a valid surrogate
				if eBonus != BonusTypes.NO_BONUS:
					setBonusType = pPlot.setBonusType
					setBonusType(BonusTypes.NO_BONUS)
					canHaveBonus = pPlot.canHaveBonus
					if not canHaveBonus(eBonus, True):
						if getBonusInfo(eBonus).getYieldChange(YieldTypes.YIELD_FOOD) > 0:
							iPossibleTempFoodBonuses = []
							for iLoopBonus in xrange(gc.getNumBonusInfos()):
								if getBonusInfo(iLoopBonus).getYieldChange(YieldTypes.YIELD_FOOD) > 0:
									if canHaveBonus(iLoopBonus, True):
										iPossibleTempFoodBonuses.append(iLoopBonus)
							setBonusType(eBonus)
							if len(iPossibleTempFoodBonuses) > 0:
								setTempB(iPossibleTempFoodBonuses[dice.get(len(iPossibleTempFoodBonuses), "End of Winter Food Thawing")], iTurns)
							else:
								setTempB(BonusTypes.NO_BONUS, iTurns)
						else:
							setBonusType(eBonus)
							setTempB(BonusTypes.NO_BONUS, iTurns)
					else:
						setBonusType(eBonus)
			# FlavourMod: End Add

		#Begin clearing starting locations of dangerous spots, like Mana Guardians and Lairs
		iDungeonRange = 5
		iGuardianRange = 5

		print('Begin Clearing')

		for iPlot in xrange(iNumPlots):
			pPlot = plotByIndex(iPlot)

			#Searching for initial settlers
			for iUnit in xrange(pPlot.getNumUnits()):
				pUnit = pPlot.getUnit(iUnit)
				if pUnit.getUnitClassType() == getInfoType("UNITCLASS_SETTLER") or pUnit.getUnitClassType() == getInfoType("UNITCLASS_VESSEL_DTESH") or pUnit.getUnitClassType() == getInfoType("UNITCLASS_AWAKENED"):
					pCurPlayer = gc.getPlayer(pUnit.getOwner())

					print('Found Settler at %d,%d - Player %d (%s)' % (pUnit.getX(), pUnit.getY(), pUnit.getOwner(), pCurPlayer.getName()))
				#	if not pCurPlayer.isHuman():
				#		iDungeonRange *= 2
				#		iGuardianRange *= 2

					#Clearing Lairs
					print('Clearing Lairs')
					for iX in range(pUnit.getX()-iDungeonRange+1, pUnit.getX()+iDungeonRange, 1):
						for iY in range(pUnit.getY()-iDungeonRange+1, pUnit.getY()+iDungeonRange, 1):
							pDangerousPlot = map.plot(iX, iY)
							print('Checking plot %d,%d' % (pDangerousPlot.getX(), pDangerousPlot.getY()))
							if pDangerousPlot.getImprovementType() != -1:
								pImprovement = gc.getImprovementInfo(pDangerousPlot.getImprovementType())
								print("Found improvement: %s" % pImprovement.getDescription())
								if pImprovement.getSpawnUnitType() != -1:
									pDangerousPlot.setImprovementType(-1)
									print("Improvement removed")
								elif pImprovement.getSpawnGroupType() != -1:
									pDangerousPlot.setImprovementType(-1)
									print("Improvement removed")
								elif pImprovement.getImmediateSpawnUnitType() != -1:
									pDangerousPlot.setImprovementType(-1)
									print("Improvement removed")
								elif pImprovement.getImmediateSpawnGroupType() != -1:
									pDangerousPlot.setImprovementType(-1)
									print("Improvement removed")

					#Clearing Mana Guardians
					print('Clearing Units')
					for iX in range(pUnit.getX()-iGuardianRange+1, pUnit.getX()+iGuardianRange, 1):
						for iY in range(pUnit.getY()-iGuardianRange+1, pUnit.getY()+iGuardianRange, 1):
							pDangerousPlot = map.plot(iX,iY)
							print('Checking plot %d,%d' % (pDangerousPlot.getX(), pDangerousPlot.getY()))
							for iDangerousUnit in range(pDangerousPlot.getNumUnits()-1,-1,-1):
								pDangerousUnit = pDangerousPlot.getUnit(iDangerousUnit)
								pDangerousPlayer = gc.getPlayer(pDangerousUnit.getOwner())
								print("Found unit: %s (%s)" % (gc.getUnitInfo(pDangerousUnit.getUnitType()).getDescription(), pDangerousPlayer.getName()))
								if gc.getTeam(pCurPlayer.getTeam()).isAtWar(pDangerousPlayer.getTeam()):
									pDangerousUnit.kill(False, -1)
									print("Unit killed")

		print('End Clearing')
		#End of clearing

		ScorpClan 	= self.Units["Scorpion Clan"]
		Civ 		= self.Civilizations
		Trait 		= self.Traits
		Lair 		= self.Lairs

		bPlayer 	= getPlayer(gc.getORC_PLAYER())
		iAnimalTeam = gc.getANIMAL_TEAM()
		initUnit 	= bPlayer.initUnit
		for i in xrange(iNumPlots):
			pPlot = plotByIndex(i)
			iImprovement = pPlot.getImprovementType()
			if iImprovement == Lair["Goblin Camp"]:
				if not Option["No Barbarians"]:
					initUnit( ScorpClan["Archer"], pPlot.getX(), pPlot.getY(), iNoAI, iSouth)
			if iImprovement == gc.getInfoTypeForString("IMPROVEMENT_WELL_OF_SOULS"):
				for iX, iY in aoeByMapSize(pPlot):
					pDangerousPlot = map.plot(iX, iY)
					if not pDangerousPlot.isWater():
						pDangerousPlot.setTerrainType(gc.getInfoTypeForString("TERRAIN_WASTELAND"),True,True)

		for iPlayer in xrange(iMaxPlayers):
			player = getPlayer(iPlayer)
			if (player.isAlive() and player.isHuman()):
				if player.getCivilizationType() == Civ["Elohim"]:
					showUniqueImprovements(iPlayer)

			if (player.isAlive()):
				if player.hasTrait(Trait["Feral"]):
					pTeam = gc.getTeam(player.getTeam())
					pTeam.makePeace(iAnimalTeam)
				if player.hasTrait(Trait["Aspect Capria"]):
					gc.getGame().setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_CAPRIA'),True)
				if player.hasTrait(Trait["Aspect Mahon"]):
					gc.getGame().setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_MAHON'),True)
				if (player.getLeaderType()==gc.getInfoTypeForString('LEADER_SAUROS') and player.getCivilizationType()!=gc.getInfoTypeForString("CIVILIZATION_CLAN_OF_EMBERS")):
					player.setNumMaxTraitPerClass(getInfoType('TRAITCLASS_SAVAGE'),0)
					
		if (game.getGameTurnYear() == self.Defines["Start Year"] and not Option["Advanced Start"]):
			if not game.getWBMapScript():
				for iPlayer in xrange(iMaxPlayers):
					player = getPlayer(iPlayer)
					if (player.isAlive() and player.isHuman()):
						popupInfo = CyPopupInfo()
						popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
						popupInfo.setText(u"showDawnOfMan")
						popupInfo.addPopup(iPlayer)
		else:
			CyInterface().setSoundSelectionReady(True)

		if game.isPbem():
			for iPlayer in xrange(iMaxPlayers):
				player = gc.getPlayer(iPlayer)
				if (player.isAlive() and player.isHuman()):
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_DETAILS)
					popupInfo.setOption1(True)
					popupInfo.addPopup(iPlayer)

		CvAdvisorUtils.resetNoLiberateCities()
		if (not Option["No Orthus"]):
			gc.getGame().setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_ORTHUS'),True)	
			
# FF Wilderness
		if Option["Dark Forests"]:
			pPlayer  = getPlayer(gc.getANIMAL_PLAYER())
			Terrain = self.Terrain
			Feature = self.Feature
			initUnit = pPlayer.initUnit
			iRnd 	 = randNum(100, "Wilderness chance")
			if iRnd < 55:
				iBestValue = 0
				pBestPlot = -1
				for i in xrange(iNumPlots):
					iValue = 0
					pPlot = plotByIndex(i)
					iFeature = pPlot.getFeatureType()
					if not pPlot.isWater():
						if (iFeature == Feature["Forest"] or iFeature == Feature["Jungle"]):
								iValue = randNum(1000, "Looking for Blighted Forest spot")
								if not pPlot.isOwned():
									iValue += 1000
								if (pPlot.getNumUnits()>0):
									iValue=0
								if (pPlot.getImprovementType()!=-1 and gc.getImprovementInfo(pPlot.getImprovementType()).isPermanent()):
									iValue=0
								if iValue > iBestValue:
									iBestValue = iValue
									pBestPlot = pPlot
				if pBestPlot != -1:
				#	iForestCreeper = Animal["Forest Creeper"]
					iX = pBestPlot.getX(); iY = pBestPlot.getY();
					newUnit = initUnit(Animal["Malignant Flora"], iX, iY, iNoAI, iSouth)
				#	newUnit = initUnit(iForestCreeper, iX, iY, iNoAI, iSouth)
				#	newUnit = initUnit(iForestCreeper, iX, iY, iNoAI, iSouth)
				#	newUnit = initUnit(iForestCreeper, iX, iY, iNoAI, iSouth)
				#	newUnit = initUnit(iForestCreeper, iX, iY, iNoAI, iSouth)
				#	newUnit = initUnit(iForestCreeper, iX, iY, iNoAI, iSouth)
				#	newUnit = initUnit(iForestCreeper, iX, iY, iNoAI, iSouth)
				#	newUnit = initUnit(iForestCreeper, iX, iY, iNoAI, iSouth)
					pBestPlot.setImprovementType(Lair["Blighted Forest"])
			if iRnd >= 45:
				iBestValue 	= 0
				pBestPlot 	= -1
				for i in xrange(iNumPlots):
					iValue = 0
					pPlot = plotByIndex(i)
					if not pPlot.isWater():
						iFeature = pPlot.getFeatureType()
						if (iFeature == Feature["Forest"] or iFeature == Feature["Jungle"] or pPlot.getTerrainType() == Terrain["Desert"]):
								iValue = randNum(1000, "Diakonos placement spot")
								if not pPlot.isOwned():
									iValue += 1000
								if (pPlot.getNumUnits()>0):
									iValue=0
								if iValue > iBestValue:
									iBestValue = iValue
									pBestPlot = pPlot
				if pBestPlot != -1:
					iDiakonos = Animal["Diakonos"]
					iX = pBestPlot.getX(); iY = pBestPlot.getY()
					newUnit = initUnit(iDiakonos, iX, iY, iNoAI, iSouth)
					newUnit = initUnit(iDiakonos, iX, iY, iNoAI, iSouth)
					newUnit = initUnit(iDiakonos, iX, iY, iNoAI, iSouth)
					newUnit = initUnit(iDiakonos, iX, iY, iNoAI, iSouth)
					newUnit = initUnit(iDiakonos, iX, iY, iNoAI, iSouth)

# FF end Wilderness

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onGameStart']:
			module.onGameStart(self, argsList)

		## Modular Python End
		## *******************

# FF: Added by Jean Elcard 14/01/2009 (speed tweak)
		rebuildGraphics()
# FF: End Add

	def onGameEnd(self, argsList):
		'Called at the End of the game'
		print("Game is ending")

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onGameEnd']:
			module.onGameEnd(self, argsList)

		## Modular Python End
		## *******************

		return

	def onBeginGameTurn(self, argsList):
		'Called at the beginning of the end of each turn'
		iGameTurn = argsList[0]

		gc = CyGlobalContext()
		getInfoType		= gc.getInfoTypeForString
		cf			= self.cf
		game 		= CyGame()
		map 		= CyMap()
		isOption 	= game.isOption
		getPlayer 	= gc.getPlayer
		iOrcPlayer 	= gc.getORC_PLAYER()

		if iGameTurn == 3:
			if not game.isNetworkMultiPlayer():
				t = "TROPHY_FEAT_INTRODUCTION"
				if not game.isHasTrophy(t):
					game.changeTrophyValue(t, 1)
					addPopupWB(CyTranslator().getText("TXT_KEY_FFH_INTRO",()),'art/interface/popups/FfHIntro.dds')

		iOrthusTurn = 75 #test
		isMaxedOut	= game.isUnitClassMaxedOut
		eSpeed		= game.getGameSpeedType()
		Speed		= self.GameSpeeds
		Trait       = self.Traits
		if not isMaxedOut(self.UnitClasses["Orthus"], 0):
			if not isOption(self.GameOptions["No Orthus"]):
				bOrthus = False
				if eSpeed == Speed["Quick"]:
					if iGameTurn >= iOrthusTurn / 3 * 2: bOrthus = True
				elif eSpeed == Speed["Normal"]:
					if iGameTurn >= iOrthusTurn: 		 bOrthus = True
				elif eSpeed == Speed["Epic"]:
					if iGameTurn >= iOrthusTurn * 3 / 2: bOrthus = True
				elif eSpeed == Speed["Marathon"]:
					if iGameTurn >= iOrthusTurn * 3: 	 bOrthus = True
				
				# EmergentLeaders: if Rizuruk is in game, Orthus goes to her
				if bOrthus:
					iPlayer     = iOrcPlayer
					if getInfoType("MODULE_EMERGENT_LEADERS")!=-1:
						iMaxPlayers = gc.getMAX_PLAYERS()
						for iLoopPlayer in xrange(iMaxPlayers):
							pLoopPlayer = getPlayer(iLoopPlayer)
							if pLoopPlayer.isAlive():
								if pLoopPlayer.hasTrait(Trait["Matriarch 1"]):
									iPlayer = iLoopPlayer					
					addUnit(self.Heroes["Orthus"], iPlayer)

		iZarcazTurn = 100
		if not isMaxedOut(self.UnitClasses["Zarcaz"], 0):
			if not isOption(self.GameOptions["No Orthus"]):
				bZarcaz = False
				if eSpeed == Speed["Quick"]:
					if iGameTurn >= iZarcazTurn / 3 * 2: bZarcaz = True
				elif eSpeed == Speed["Normal"]:
					if iGameTurn >= iZarcazTurn: 		 bZarcaz = True
				elif eSpeed == Speed["Epic"]:
					if iGameTurn >= iZarcazTurn * 3 / 2: bZarcaz = True
				elif eSpeed == Speed["Marathon"]:
					if iGameTurn >= iZarcazTurn * 3: 	 bZarcaz = True
				if bZarcaz:
					addUnit(self.Heroes["Zarcaz"], iOrcPlayer)
					Race 		= self.Promotions["Race"]
					Equipment 	= self.Promotions["Equipment"]
					Unit = self.Units["Scorpion Clan"]

					pPlayer = getPlayer(iOrcPlayer)
					py = PyPlayer(iOrcPlayer)
					iNoAI = UnitAITypes.NO_UNITAI
					iSouth = DirectionTypes.DIRECTION_SOUTH
					initUnit = pPlayer.initUnit
					for pUnit in py.getUnitList():
						if (pUnit.getRace() == Race["Goblinoid"] and pUnit.isHasPromotion(Equipment["Zarcazs Bow"]) == True):
							pPlot = pUnit.plot()
							iX = pPlot.getX(); iY = pPlot.getY()

							newUnit2 = initUnit(Unit["Archer"], iX, iY, iNoAI, iSouth)
							pUnit.addMinion(newUnit2)

							newUnit3 = initUnit(Unit["Goblin"], iX, iY, iNoAI, iSouth)
							pUnit.addMinion(newUnit3)

							newUnit4 = initUnit(Unit["Wolf Rider"], iX, iY, iNoAI, iSouth)
							pUnit.addMinion(newUnit4)
		
		bPlayer = gc.getPlayer(gc.getDEMON_PLAYER())
		if (iGameTurn + 1) % (40- 5*CyGame().getGameSpeedType()) == 0 and not bPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_CONTROLED_LACUNA')):
			iRnd = 4 - CyGame().getGameSpeedType()
			iBB = gc.getInfoTypeForString('IMPROVEMENT_BAIR_OF_LACUNA')
			lBB = cf.findImprovements(iBB)
			if len(lBB) > 0:
				pPlotBB = lBB[0]
				iIce = gc.getInfoTypeForString('BONUS_MANA_DIMENSIONAL')
				iBestValue = 0
				pBestPlot = -1
				for i in xrange (CyMap().numPlots()):
					pTargetPlot = CyMap().plotByIndex(i)
					if pTargetPlot == pPlotBB:
						continue
					if pTargetPlot.isPeak():
						continue
					if pTargetPlot.isWater():
						continue
					if pTargetPlot.getBonusType(-1) != -1:
						continue
					iValue = 0
					iImp = pTargetPlot.getImprovementType()
					if iImp == -1:
						iValue += 1000
					elif gc.getImprovementInfo(iImp).isPermanent():
						continue
					iValue += CyGame().getSorenRandNum(1000, "Bair move ")
					if not pTargetPlot.isOwned():
						iValue += 500
					if iValue > iBestValue:
						iBestValue = iValue
						pBestPlot = pTargetPlot
				if pBestPlot != -1:
				#   For the Guardian
				#	iBadb = gc.getInfoTypeForString('UNIT_BADB')
				#	for i in xrange(pPlotBB.getNumUnits()):
				#		pUnit = pPlotBB.getUnit(i)
				#		if iBadb in [pUnit.getUnitType()]:
				#			pUnit.setXY(pBestPlot.getX(), pBestPlot.getY(), False, True, True)
				#			break

					iBonusReal = pPlotBB.getRealBonusType()
					if iBonusReal == iIce:
						pPlotBB.setBonusType(-1)
					else:
						pPlotBB.setBonusType(iBonusReal)
				#	if (pPlotBB.getTempTerrainTimer()>0):
				#		pPlotBB.changeTempTerrainTimer(1-pPlotBB.getTempTerrainTimer())
				#	iReal = pPlotBB.getRealImprovementType()
				#	if iReal == iBB:
					pPlotBB.setImprovementType(-1)
				#	else:
				#		pPlotBB.setImprovementType(iReal)

					pBestPlot.setTempBonusType(iIce, iRnd)
					pBestPlot.setExploreNextTurn(pPlotBB.getExploreNextTurn())
					pPlotBB.setExploreNextTurn(0)

					pBestPlot.setImprovementType(iBB)
					pBestPlot.setBonusType(iIce)
				#	pBestPlot.setFeatureType(iBl, 0)

# FfH Card Game: begin
		cs.doTurn()
# FfH Card Game: end

		cf.doFFTurn()
		if game.getWBMapScript():
			sf.doTurn()


		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onBeginGameTurn']:
			module.onBeginGameTurn(self, argsList)

		## Modular Python End
		## *******************

#Added in Frozen: TC01 (Blizzard Utils)
		Blizzards.doBlizzardTurn()
#End of Frozen

		if game.getAIAutoPlay() == 0:
			CvTopCivs.CvTopCivs().turnChecker(iGameTurn)

	def onEndGameTurn(self, argsList):
		'Called at the end of the end of each turn'
		iGameTurn = argsList[0]

		gc = CyGlobalContext()
		game = CyGame()
		map = CyMap()
		getPlayer = gc.getPlayer
		iDemonTeam = gc.getDEMON_TEAM()

# FF: Added by Jean Elcard 14/01/2009 (speed tweak)
		rebuildGraphics()
# FF: End Add

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onEndGameTurn']:
			module.onEndGameTurn(self, argsList)

		## Modular Python End
		## *******************


		if game.isVictoryValid(self.Victories["Gone to Hell"]):
			iMaxPlayers = gc.getMAX_PLAYERS()
			iTotalTiles = map.numPlots()
			iEvilTiles = 0

			for iLoop in xrange(map.getNumAreas()):
				iEvilTiles += map.getArea(iLoop).getNumEvilTiles()


			if (100.0 * iEvilTiles) / iTotalTiles > self.Defines["Gone to Hell"]:

				pMostEvilPlayer = -1
				iMostEvilTotalContrib = 0

				for iLoopPlayer in xrange(iMaxPlayers):
					pLoopPlayer = getPlayer(iLoopPlayer)
					if pLoopPlayer.isAlive():
						if pLoopPlayer.getGlobalCounterContrib() > iMostEvilTotalContrib:
							pMostEvilPlayer = pLoopPlayer
							iMostEvilTotalContrib = pLoopPlayer.getGlobalCounterContrib()

				if pMostEvilPlayer != -1:
					pMostEvilPlayer.setTeam(iDemonTeam)

				game.setWinner(iDemonTeam, self.Victories["Gone to Hell"])

		if FoxGlobals["USE_AIAUTOPLAY_SOUND"]:
			if game.getAIAutoPlay() == 1:
				pCapital = getPlayer(0).getCapitalCity().plot()
				if pCapital != None:
					CyCamera().JustLookAtPlot(pCapital)
					point 			= pCapital.getPoint()
					profile			= CyUserProfile()
					Play3DSound		= CyAudioGame().Play3DSound
					profile.setMasterNoSound(False)
					profile.setMasterVolume(50)
					profile.setSpeechVolume(50)
					Play3DSound("AS3D_ENGLAND_SELECT",point.x,point.y,point.z)
					profile.setMasterVolume(SoundSettings["SOUND_MASTER_VOLUME"])
					profile.setSpeechVolume(SoundSettings["SOUND_SPEECH_VOLUME"])
					profile.setMasterNoSound(SoundSettings["SOUND_MASTER_NO_SOUND"])

	def onBeginPlayerTurn(self, argsList):
		'Called at the beginning of a players turn'
		iGameTurn, iPlayer = argsList
		gc 				= CyGlobalContext()
		cf				= self.cf
		game 			= CyGame()
		getPlayer 		= gc.getPlayer
		iDemonTeam 		= gc.getDEMON_TEAM()
		pPlayer 		= getPlayer(iPlayer)
		bAI		 		= self.Tools.isAI(iPlayer)
		hasTrait 		= pPlayer.hasTrait
		isCivic 		= pPlayer.isCivic
		randNum 		= game.getSorenRandNum

		eCiv 			= pPlayer.getCivilizationType()
		eSpeed 			= game.getGameSpeedType()
		Civ				= self.Civilizations
		Civic			= self.Civics
		Trait			= self.Traits
		Speed			= self.GameSpeeds
		Status			= self.LeaderStatus
		Event			= self.EventTriggers
		Define			= self.Defines
		trigger			= pPlayer.trigger
		triggerData		= pPlayer.initTriggeredData

		print ("GameTurn: "+str(iGameTurn))
	##	print (PyPlayer(iPlayer).getCivilizationName())


		if bAI and not game.getWBMapScript():   cf.warScript(iPlayer)
		if isCivic(Civic["Crusade"]):           cf.doCrusade(iPlayer)

		if   eCiv == Civ["Khazad"]:             cf.doTurnKhazad(iPlayer)
		elif eCiv == Civ["Luchuirp"]:           cf.doTurnLuchuirp(iPlayer)
		elif eCiv == Civ["Archos"]:             cf.doTurnArchos(iPlayer)
		elif eCiv == Civ["Scions"]:             cf.doTurnScions(iPlayer)
		elif eCiv == Civ["Grigori"]:            cf.doTurnGrigori(iPlayer)
		elif eCiv == Civ["Mekara Order"]:       cf.doTurnMekara(iPlayer)
		elif eCiv == Civ["Cualli"]:             cf.doTurnCualli(iPlayer)
		elif eCiv == Civ["Infernal"]:
			if not gc.isNoCrash():
				game.releasefromDeathList(gc.getInfoTypeForString('DEATHLIST_DEMON_CONVERSION'),iPlayer,6,gc.getInfoTypeForString('UNIT_MANES'))
				game.releasefromDeathList(gc.getInfoTypeForString('DEATHLIST_DEMON_REBIRTH'),iPlayer,0,-1)
			
		elif eCiv == Civ["Mercurians"]:
			if not gc.isNoCrash():
				game.releasefromDeathList(gc.getInfoTypeForString('DEATHLIST_ANGEL_CONVERSION'),iPlayer,1,gc.getInfoTypeForString('UNIT_ANGEL'))
		if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_INSANE")) and CyGame().getSorenRandNum(50, "Insane Trait Roll") == 0:
			lTraits = []
			for iTrait in xrange(gc.getNumTraitInfos()):
				if gc.getTraitInfo(iTrait).isSelectable() and iTrait != gc.getInfoTypeForString("TRAIT_INSANE"):
					if not gc.isNoCrash():
						pPlayer.setHasTrait((iTrait),False,-1,True,True)
					else:
						pPlayer.setHasTrait((iTrait),False)
					lTraits.append(iTrait)
			if len(lTraits) >= 3:
				iTrait1, iTrait2, iTrait3 = -1, -1, -1
				iTrait1 = lTraits[CyGame().getSorenRandNum(len(lTraits), "Insane Trait 1")]
				while iTrait2 == -1 or iTrait2 == iTrait1:
					iTrait2 = lTraits[CyGame().getSorenRandNum(len(lTraits), "Insane Trait 2")]
				while iTrait3 == -1 or iTrait3 == iTrait1 or iTrait3 == iTrait2:
					iTrait3 = lTraits[CyGame().getSorenRandNum(len(lTraits), "Insane Trait 3")]
				if not gc.isNoCrash():
					pPlayer.setHasTrait((iTrait1),True,-1,True,True)
					pPlayer.setHasTrait((iTrait2),True,-1,True,True)
					pPlayer.setHasTrait((iTrait3),True,-1,True,True)
				else:
					pPlayer.setHasTrait((iTrait1),True)
					pPlayer.setHasTrait((iTrait2),True)
					pPlayer.setHasTrait((iTrait3),True)
				pCapital = pPlayer.getCapitalCity()
				if pCapital != -1:
					iColor		= CyGame().getSorenRandNum(123, "Insane Color Pick")
					szMessage	= CyTranslator().getText("TXT_KEY_INSANE_HELP", (gc.getTraitInfo(iTrait1).getDescription(), gc.getTraitInfo(iTrait2).getDescription(), gc.getTraitInfo(iTrait3).getDescription(),))
					lIcon		= ["Art/Interface/Buttons/General/happy_person.dds","Art/Interface/mainscreen/cityscreen/angry_citizen.dds","Art/Interface/Buttons/General/unhealthy_person.dds","Art/Interface/Buttons/WorldBuilder/Crab.dds"]
					iIcon		= lIcon[CyGame().getSorenRandNum(len(lIcon), "Insane Icon Pick")]
					CyInterface().addMessage(iPlayer,True,25,szMessage,'',3,iIcon,ColorTypes(iColor),pCapital.getX(),pCapital.getY(),True,True)
				iRand4 = CyGame().getSorenRandNum(100,"Insane")
				if (iRand4<10):
					pPlayer.setHasFlag(gc.getInfoTypeForString("FLAG_PERPENTACH_BODY_SWITCH"),True)
		if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_ADAPTIVE")):
			iCycle = gc.getGameSpeedInfo(gc.getGame().getGameSpeedType()).getGrowthPercent() - 5
			if iGameTurn % iCycle == 0:
				git				= gc.getInfoTypeForString
				lDirtyTraits	= [git("TRAIT_AGGRESSIVE"),git("TRAIT_ARCANE"),git("TRAIT_CHARISMATIC"),git("TRAIT_CREATIVE"),git("TRAIT_EXPANSIVE"),git("TRAIT_FINANCIAL"),git("TRAIT_INDUSTRIOUS"),git("TRAIT_ORGANIZED"),git("TRAIT_PHILOSOPHICAL"),git("TRAIT_RAIDERS"),git("TRAIT_SPIRITUAL")]
				lWidgetTraits	= ["TRAIT_AGGRESSIVE","TRAIT_ARCANE","TRAIT_CHARISMATIC","TRAIT_CREATIVE","TRAIT_EXPANSIVE","TRAIT_FINANCIAL","TRAIT_INDUSTRIOUS","TRAIT_ORGANIZED","TRAIT_PHILOSOPHICAL","TRAIT_RAIDERS","TRAIT_SPIRITUAL"]
				if pPlayer.isHuman():
					popupInfo	= CyPopupInfo()
					popupInfo.setOption2(True)
					popupInfo.setFlags(165) # Trait widget on mouseover
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
					popupInfo.setOnClickedPythonCallback("passToModNetMessage")
					popupInfo.setData1(iPlayer)
					popupInfo.setData3(100) # onModNetMessage id
					popupInfo.setText(CyTranslator().getText("TXT_KEY_EVENTTRIGGER_TRAIT_ADAPTIVE", ()))
					for iTrait in lDirtyTraits:
						iIndex = lDirtyTraits.index(iTrait)
						if pPlayer.hasTrait(iTrait) and gc.getLeaderHeadInfo(pPlayer.getLeaderType()).getPermanentTrait() != iTrait:	# Reset iTrait
							if not gc.isNoCrash():
								pPlayer.setHasTrait((iTrait),False,-1,True,True)
							else:
								pPlayer.setHasTrait((iTrait),False)
						if not pPlayer.hasTrait(iTrait):																				# Set iTrait to the pick list
							popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_ADAPTIVE_HELP", (gc.getTraitInfo(iTrait).getDescription(),)),lWidgetTraits[iIndex])
					popupInfo.addPopup(iPlayer)
				else:
					lTraits = []
					for iTrait in lDirtyTraits:
						if pPlayer.hasTrait(iTrait) and gc.getLeaderHeadInfo(pPlayer.getLeaderType()).getPermanentTrait() != iTrait:	# Reset iTrait
							if not gc.isNoCrash():
								pPlayer.setHasTrait((iTrait),False,-1,True,True)
							else:
								pPlayer.setHasTrait((iTrait),False)
						if not pPlayer.hasTrait(iTrait):
							lTraits.append(iTrait)
					if lTraits:
						AITrait = lTraits[CyGame().getSorenRandNum(len(lTraits), "AI Adaptive Trait Roll")]
						if not gc.isNoCrash():
							pPlayer.setHasTrait((AITrait),True,-1,True,True)
						else:
							pPlayer.setHasTrait((AITrait),True)

	#	if pPlayer.getLeaderStatus() == Status["Important"]:
	#		if pPlayer.getPlayersKilled() >= 1 and not hasTrait(Trait["Aggressive"]):
	#			triggerData( Event["Aggressive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

	#	if hasTrait(Trait["Horde"]): # Barbarians declare war on the Clan if it becomes too strong; re-added by Azatote
	#		eTeam = gc.getTeam(gc.getPlayer(gc.getORC_PLAYER()).getTeam())
	#		iTeam = pPlayer.getTeam()
	#		getScore = game.getPlayerScore
	#		if eTeam.isAtWar(iTeam) == False:
	#			if getScore(iPlayer) >= 1.5 * getScore(game.getRankPlayer(1)):
	#				if iGameTurn >= 20:
	#					eTeam.declareWar(iTeam, False, WarPlanTypes.WARPLAN_LIMITED)
	#					if (iPlayer == game.getActivePlayer() and not bAI):
	#						addPopup(CyTranslator().getText("TXT_KEY_POPUP_BARBARIAN_DECLARE_WAR",()), 'art/interface/popups/Barbarian.dds')

		# Republic Start

		if pPlayer.getCivics(gc.getInfoTypeForString("CIVICOPTION_GOVERNMENT")) == gc.getInfoTypeForString("CIVIC_REPUBLIC"):
			pPlayer.changeFlagValue(gc.getInfoTypeForString("FLAG_REPUBLIC_TIMER"), 1)
			iCycle = gc.getGameSpeedInfo(gc.getGame().getGameSpeedType()).getGrowthPercent() / 10 * 4
			if pPlayer.getFlagValue(gc.getInfoTypeForString("FLAG_REPUBLIC_TIMER")) == iCycle:
				pPlayer.setFlagValue(gc.getInfoTypeForString("FLAG_REPUBLIC_TIMER"), 0)
			if pPlayer.getFlagValue(gc.getInfoTypeForString("FLAG_REPUBLIC_TIMER")) == 1:
				for iTrait in xrange(gc.getNumTraitInfos()):
					if gc.getTraitInfo(iTrait).getTraitClass() == gc.getInfoTypeForString("TRAITCLASS_REPUBLIC"):
						if not gc.isNoCrash():
							pPlayer.setHasTrait((iTrait),False,-1,True,True)
						else:
							pPlayer.setHasTrait((iTrait),False)
				iElection = CyGame().getSorenRandNum(4, "Republic Election Type")
				if pPlayer.isHuman():
					lText = []
					if iElection == 0:
						lText = ["TXT_KEY_EVENTTRIGGER_REPUBLIC_ELECTION_HAWK_VS_DOVE","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_HAWK","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_DOVE","TXT_KEY_EVENT_REPUBLIC_ELECTION_FAIR_HAWK_VS_DOVE"]
						lWidget = ['EVENT_REPUBLIC_ELECTION_SUPPORT_HAWK','EVENT_REPUBLIC_ELECTION_SUPPORT_DOVE','EVENT_REPUBLIC_ELECTION_FAIR_HAWK_VS_DOVE']
					if iElection == 1:
						lText = ["TXT_KEY_EVENTTRIGGER_REPUBLIC_ELECTION_LANDOWNER_VS_PEASANTS","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_LANDOWNER","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_PEASANT","TXT_KEY_EVENT_REPUBLIC_ELECTION_FAIR_LANDOWNER_VS_PEASANT"]
						lWidget = ['EVENT_REPUBLIC_ELECTION_SUPPORT_LANDOWNER','EVENT_REPUBLIC_ELECTION_SUPPORT_PEASANT','EVENT_REPUBLIC_ELECTION_FAIR_LANDOWNER_VS_PEASANT']
					if iElection == 2:
						lText = ["TXT_KEY_EVENTTRIGGER_REPUBLIC_ELECTION_CHURCH_VS_STATE","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_CHURCH","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_STATE","TXT_KEY_EVENT_REPUBLIC_ELECTION_FAIR_CHURCH_VS_STATE"]
						lWidget = ['EVENT_REPUBLIC_ELECTION_SUPPORT_CHURCH','EVENT_REPUBLIC_ELECTION_SUPPORT_STATE','EVENT_REPUBLIC_ELECTION_FAIR_CHURCH_VS_STATE']
					if iElection == 3:
						lText = ["TXT_KEY_EVENTTRIGGER_REPUBLIC_ELECTION_LABOR_VS_ACADEMIA","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_LABOR","TXT_KEY_EVENT_REPUBLIC_ELECTION_SUPPORT_ACADEMIA","TXT_KEY_EVENT_REPUBLIC_ELECTION_FAIR_LABOR_VS_ACADEMIA"]
						lWidget = ['EVENT_REPUBLIC_ELECTION_SUPPORT_LABOR','EVENT_REPUBLIC_ELECTION_SUPPORT_ACADEMIA','EVENT_REPUBLIC_ELECTION_FAIR_LABOR_VS_ACADEMIA']
					popupInfo = CyPopupInfo()
					popupInfo.setOption2(True)
					popupInfo.setFlags(126) # Event widget on mouseover
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
					popupInfo.setOnClickedPythonCallback("passToModNetMessage")
					popupInfo.setData1(iPlayer)
					popupInfo.setData2(iElection)
					popupInfo.setData3(101) # onModNetMessage id
					popupInfo.setText(CyTranslator().getText(lText[0], ()))
					popupInfo.addPythonButton(CyTranslator().getText(lText[1], ()),lWidget[0])
					popupInfo.addPythonButton(CyTranslator().getText(lText[2], ()),lWidget[1])
					popupInfo.addPythonButton(CyTranslator().getText(lText[3], ()),lWidget[2])
					popupInfo.addPopup(iPlayer)
				else:
					argsList = [2,iPlayer,iElection]
					CvScreensInterface.effectRepublic(argsList) # based on iAIValue of events (always fair)

		# Republic End

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onBeginPlayerTurn']:
			module.onBeginPlayerTurn(self, argsList)

		## Modular Python End
		## *******************

		if pPlayer.isHuman():
			self.Tools.showTraitPopup()

	def onEndPlayerTurn(self, argsList):
		'Called at the end of a players turn'
		iGameTurn, iPlayer = argsList
		gc 			= CyGlobalContext()
		cf			= self.cf
		game 		= CyGame()
		getPlayer 	= gc.getPlayer
		pPlayer 	= getPlayer(iPlayer)

		if (game.getElapsedGameTurns() == 1):
			if (pPlayer.isHuman()):
				if (pPlayer.canRevolution(0)):
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_CHANGECIVIC)
					popupInfo.addPopup(iPlayer)

		CvAdvisorUtils.resetAdvisorNags()
		CvAdvisorUtils.endTurnFeats(iPlayer)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onEndPlayerTurn']:
			module.onEndPlayerTurn(self, argsList)

		## Modular Python End
		## *******************

# FF: Added by Jean Elcard 14/01/2009 (speed tweak)
		rebuildGraphics()
# FF: End Add

	def onEndTurnReady(self, argsList):
		iGameTurn = argsList[0]

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onEndTurnReady']:
			module.onEndTurnReady(self, argsList)

		## Modular Python End
		## *******************

	def onFirstContact(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##				
		'Contact'
		iTeamX,iHasMetTeamY = argsList
		if (not self.__LOG_CONTACT):
			return
		CvUtil.pyPrint('Team %d has met Team %d' %(iTeamX, iHasMetTeamY))

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onFirstContact']:
			module.onFirstContact(self, argsList)

		## Modular Python End
		## *******************

	def onCombatResult(self, argsList):
		'Combat Result'
		pWinner,pLoser  = argsList
		gc              = CyGlobalContext()
		iWinner         = pWinner.getOwner()
		pWinnerPlayer   = gc.getPlayer(iWinner)
		iLoser         = pLoser.getOwner()
		pLoserPlayer    = gc.getPlayer(pLoser.getOwner())
		### NOW DONE IN POSTCOMBAT METHODS ON PROMOTIONS

		iGodslayer = gc.getInfoTypeForString('PROMOTION_GODSLAYER')
		iAvatar = gc.getInfoTypeForString('PROMOTION_AVATAR')
		iClava = gc.getInfoTypeForString('PROMOTION_CLAVA_VINDEX')
		iNetherblade = gc.getInfoTypeForString('PROMOTION_NETHER_BLADE')
		
		if pWinner.isHasPromotion(iGodslayer):
			if pLoser.isHasPromotion(iAvatar):
				pLoser.setHasPromotion(iAvatar, False)
				pLoser.kill(False, iWinner)
		elif pLoser.isHasPromotion(iGodslayer):
			if pWinner.isHasPromotion(iAvatar):
				pWinner.setHasPromotion(iAvatar, False)
				pWinner.kill(False, iLoser)
		
		elif pWinner.isHasPromotion(iNetherblade) and not gc.isNoCrash():
			gc.getGame().addtoDeathList(gc.getInfoTypeForString('DEATHLIST_NETHERBLADE'),pLoser)
			pLoser.kill(False, iWinner)
		elif pLoser.isHasPromotion(iNetherblade) and not gc.isNoCrash():
			gc.getGame().addtoDeathList(gc.getInfoTypeForString('DEATHLIST_NETHERBLADE'),pWinner)
			pWinner.kill(False, iLoser)
			
		elif pWinner.isHasPromotion(iClava):
			
			CvUtil.pyPrint('someone was killed with a clava')
			if pLoser.isHasPromotion(gc.getInfoTypeForString('PROMOTION_DEMON')) and not gc.isNoCrash():
				gc.getGame().addtoDeathList(gc.getInfoTypeForString('DEATHLIST_BASIUM_DEMON'),pLoser)
				pLoser.kill(False, iWinner)
				CvUtil.pyPrint('a demon was killed with a clava')
				
			if cf.angelorMane(pLoser) == gc.getInfoTypeForString('UNIT_MANES') and not gc.isNoCrash():
				gc.getGame().addtoDeathList(gc.getInfoTypeForString('DEATHLIST_BASIUM'),pLoser)
				pLoser.kill(False, iWinner)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCombatResult']:
			module.onCombatResult(self, argsList)

		## Modular Python End
		## *******************
		
		if (not self.__LOG_COMBAT):
			return
		
	def onCombatLogCalc(self, argsList):
		'Combat Result'
		genericArgs = argsList[0][0]
		cdAttacker = genericArgs[0]
		cdDefender = genericArgs[1]
		iCombatOdds = genericArgs[2]
		CvUtil.combatMessageBuilder(cdAttacker, cdDefender, iCombatOdds)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCombatLogCalc']:
			module.onCombatLogCalc(self, argsList)

		## Modular Python End
		## *******************

	def onCombatLogHit(self, argsList):
		'Combat Message'
		global gCombatMessages, gCombatLog
		gc 			= CyGlobalContext()
		genericArgs = argsList[0][0]
		cdAttacker = genericArgs[0]
		cdDefender = genericArgs[1]
		iIsAttacker = genericArgs[2]
		iDamage = genericArgs[3]

		if cdDefender.eOwner == cdDefender.eVisualOwner:
			szDefenderName = gc.getPlayer(cdDefender.eOwner).getNameKey()
		else:
			szDefenderName = localText.getText("TXT_KEY_TRAIT_PLAYER_UNKNOWN", ())
		if cdAttacker.eOwner == cdAttacker.eVisualOwner:
			szAttackerName = gc.getPlayer(cdAttacker.eOwner).getNameKey()
		else:
			szAttackerName = localText.getText("TXT_KEY_TRAIT_PLAYER_UNKNOWN", ())

		if (iIsAttacker == 0):
			combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_HIT", (szDefenderName, cdDefender.sUnitName, iDamage, cdDefender.iCurrHitPoints, cdDefender.iMaxHitPoints))
			CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
			CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)
			if (cdDefender.iCurrHitPoints <= 0):
				combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_DEFEATED", (szAttackerName, cdAttacker.sUnitName, szDefenderName, cdDefender.sUnitName))
				CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
				CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)
		elif (iIsAttacker == 1):
			combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_HIT", (szAttackerName, cdAttacker.sUnitName, iDamage, cdAttacker.iCurrHitPoints, cdAttacker.iMaxHitPoints))
			CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
			CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)
			if (cdAttacker.iCurrHitPoints <= 0):
				combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_DEFEATED", (szDefenderName, cdDefender.sUnitName, szAttackerName, cdAttacker.sUnitName))
				CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
				CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCombatLogHit']:
			module.onCombatLogHit(self, argsList)

		## Modular Python End
		## *******************

	def onImprovementBuilt(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Improvement Built'
		iImprovement, iX, iY = argsList
		self.verifyLoaded()
		gc = CyGlobalContext()
		map = CyMap()
		game = CyGame()
		pPlot = map.plot(iX, iY)
		Improvement = self.Improvements
		Leader = self.Leaders
		ImprovementDtesh = self.CivImprovements["D'Tesh"]
		ImprovementDwarven = self.CivImprovements["Dwarven"]
		getPlot	= CyMap().plot
		if gc.getImprovementInfo(iImprovement).isUnique():
			# This CyEngine call, for whatever godsdangnabit reason, fails to trigger when
			# a landmark has been removed from the same tile before the player has a chance to input anything.
			# So, delay a fraction of a second. Hell if I know why.
			# Defer also doesn't update until WB is exited which can cause confusion, so check for that and game init
			if (game.GetWorldBuilderMode() or game.getGameTurn() < 1):
				CyEngine().addLandmark(pPlot, CvUtil.convertToStrLatin(gc.getImprovementInfo(iImprovement).getDescription()))
			else:
				deferCall(lambda: CyEngine().addLandmark(pPlot, CvUtil.convertToStrLatin(gc.getImprovementInfo(iImprovement).getDescription())), delay=0.05)

			Unique = self.UniqueImprovements

			if   iImprovement == Unique["Ring of Carcer"]:
				pPlot.setMinLevel(15)

			elif iImprovement == Unique["Bair of Lacuna"]:
				pPlot.setMinLevel(6)
				pPlot.setRouteType(Improvement["Road"])

			elif iImprovement == gc.getInfoTypeForString("IMPROVEMENT_SEVEN_PINES"):
				for iiX, iiY in aoeByMapSize(pPlot):
					pLoopPlot = getPlot(iiX, iiY)
					pLoopPlot.setPlotEffectType(gc.getInfoTypeForString("PLOT_EFFECT_BLESSED_LANDS"))

			elif gc.getInfoTypeForString("MODULE_MAGISTER_ASHES")!=-1 and iImprovement==gc.getInfoTypeForString("IMPROVEMENT_WHISPERING_WOOD"):
				for iiX, iiY in aoeByMapSize(pPlot):
					pLoopPlot = getPlot(iiX, iiY)
					pLoopPlot.setPlotEffectType(gc.getInfoTypeForString("PLOT_EFFECT_MIST"))

		elif iImprovement == ImprovementDtesh["Aquatic Pyre"]:
			if pPlot.getFeatureType != -1:
				pPlot.setFeatureType(-1, -1)
			if pPlot.getBonusType(-1) != -1:
				pPlot.setBonusType(-1)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onImprovementBuilt']:
			module.onImprovementBuilt(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_IMPROVEMENT):
			return
		CvUtil.pyPrint('Improvement %s was built at %d, %d'
			%(PyInfo.ImprovementInfo(iImprovement).getDescription(), iX, iY))

	def onImprovementDestroyed(self, argsList):
		## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
		## Platy Builder ##
		'Improvement Destroyed'
		iImprovement, iOwner, iX, iY = argsList
		Improvement = self.Improvements
		gc = CyGlobalContext()
		getPlot	= CyMap().plot
		game = CyGame()
		map = CyMap()

		if iImprovement != -1:
			if gc.getImprovementInfo(iImprovement).isUnique():
				Unique = self.UniqueImprovements
				pPlot = map.plot(iX, iY)
				CyEngine().removeLandmark(pPlot)
				rebuildPlots([pPlot])

				if   iImprovement == Unique["Ring of Carcer"]:
					pPlot.setMinLevel(-1)

				elif iImprovement == Unique["Bair of Lacuna"]:
					pPlot.setMinLevel(-1)
					pPlot.setRouteType(-1)

				elif iImprovement == gc.getInfoTypeForString("IMPROVEMENT_SEVEN_PINES"):
					for iiX, iiY in aoeByMapSize(pPlot):
						pLoopPlot = getPlot(iiX, iiY)
						pLoopPlot.setPlotEffectType(gc.getInfoTypeForString("NO_PLOT_EFFECT"))

				elif gc.getInfoTypeForString("MODULE_MAGISTER_ASHES")!=-1 and iImprovement==gc.getInfoTypeForString("IMPROVEMENT_WHISPERING_WOOD"):
					for iiX, iiY in aoeByMapSize(pPlot):
						pLoopPlot = getPlot(iiX, iiY)
						pLoopPlot.setPlotEffectType(gc.getInfoTypeForString("NO_PLOT_EFFECT"))

			elif iImprovement == Improvement["Necrototem"]:
				game.changeGlobalCounter(-2)

		if game.getWBMapScript():
			sf.onImprovementDestroyed(iImprovement, iOwner, iX, iY)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onImprovementDestroyed']:
			module.onImprovementDestroyed(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_IMPROVEMENT):
			return
		CvUtil.pyPrint('Improvement %s was Destroyed at %d, %d'
			%(PyInfo.ImprovementInfo(iImprovement).getDescription(), iX, iY))

	def onRouteBuilt(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Route Built'
		iRoute, iX, iY = argsList
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onRouteBuilt']:
			module.onRouteBuilt(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_IMPROVEMENT):
			return
		CvUtil.pyPrint('Route %s was built at %d, %d'
			%(gc.getRouteInfo(iRoute).getDescription(), iX, iY))

	def onPlotRevealed(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##					
		'Plot Revealed'
		pPlot = argsList[0]
		iTeam = argsList[1]

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onPlotRevealed']:
			module.onPlotRevealed(self, argsList)

		## Modular Python End
		## *******************

	def onPlotFeatureRemoved(self, argsList):
		'Plot Revealed'
		pPlot = argsList[0]
		iFeatureType = argsList[1]
		pCity = argsList[2] # This can be null

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onPlotFeatureRemoved']:
			module.onPlotFeatureRemoved(self, argsList)

		## Modular Python End
		## *******************

	def onPlotPicked(self, argsList):
		'Plot Picked'
		pPlot = argsList[0]
		CvUtil.pyPrint('Plot was picked at %d, %d'
			%(iX, iY))

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onPlotPicked']:
			module.onPlotPicked(self, argsList)

		## Modular Python End
		## *******************

	def onNukeExplosion(self, argsList):
		'Nuke Explosion'
		pPlot, pNukeUnit = argsList
		CvUtil.pyPrint('Nuke detonated at %d, %d'
			%(iX, iY))

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onNukeExplosion']:
			module.onNukeExplosion(self, argsList)

		## Modular Python End
		## *******************

	def onGotoPlotSet(self, argsList):
		'Nuke Explosion'
		pPlot, iPlayer = argsList

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onGotoPlotSet']:
			module.onGotoPlotSet(self, argsList)

		## Modular Python End
		## *******************

	def onBuildingBuilt(self, argsList):
		'Building Completed'
		pCity, iBuildingType = argsList
		player = pCity.getOwner()

		gc 			= CyGlobalContext()
		cf			= self.cf
		getInfoType	= gc.getInfoTypeForString
		game 		= CyGame()
		randNum 	= game.getSorenRandNum
		getPlayer 	= gc.getPlayer
		pPlayer 	= getPlayer(player)
		getTeam		= gc.getTeam
		hasTrait 	= pPlayer.hasTrait
		iStatus 	= pPlayer.getLeaderStatus()
		iNoAI		= UnitAITypes.NO_UNITAI
		iNorth 		= DirectionTypes.DIRECTION_NORTH
		iSouth 		= DirectionTypes.DIRECTION_SOUTH
		setNumRealBuilding = pCity.setNumRealBuilding
		iX			= pCity.getX()
		iY			= pCity.getY()
		Building	= self.Buildings
		Trait		= self.Traits
		Leader		= self.Leaders
		Status		= self.LeaderStatus
		Event		= self.EventTriggers
		Civ			= self.Civilizations
		triggerData	= pPlayer.initTriggeredData
		pBuilding   = gc.getBuildingInfo(iBuildingType)
		pPlot = pCity.plot()

		iBuildingClass = pBuilding.getBuildingClassType()

		if ((not game.isNetworkMultiPlayer()) and (pCity.getOwner() == game.getActivePlayer()) and isWorldWonderClass(iBuildingClass)):
			if pBuilding.getMovie():
				## Platy Builder ##
				if not CyGame().GetWorldBuilderMode():
					# If this is a wonder...
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
					popupInfo.setData1(iBuildingType)
					popupInfo.setData2(pCity.getID())
					popupInfo.setData3(0)
					popupInfo.setText(u"showWonderMovie")
					popupInfo.addPopup(pCity.getOwner())

		if iBuildingType == Building["Infernal Grimoire"]:
			if randNum(100, "Grimoire Effect") <= 20:
				pPlot2 = findClearPlot(-1, pPlot)
				if pPlot2 != -1:
					Unit	= self.Units["Infernal"]
					bPlayer = getPlayer(gc.getDEMON_PLAYER())
					newUnit = bPlayer.initUnit(Unit["Balor"], pPlot2.getX(), pPlot2.getY(), iNoAI, iNorth)
					CyInterface().addMessage(pCity.getOwner(),True,25,CyTranslator().getText("TXT_KEY_MESSAGE_INFERNAL_GRIMOIRE_BALOR",()),'AS2D_BALOR',1,'Art/Interface/Buttons/Units/Balor.dds',ColorTypes(7),newUnit.getX(),newUnit.getY(),True,True)
					if pCity.getOwner() == game.getActivePlayer():
						addPopup(CyTranslator().getText("TXT_KEY_POPUP_INFERNAL_GRIMOIRE_BALOR",()), 'art/interface/popups/Balor.dds')

		elif iBuildingType == Building["Pact of the Nilhorn"]:
			initUnit = pPlayer.initUnit
			Unit 	 = self.Units["Savage"]
			Promo	 = self.Promotions["Effects"]
			Race	 = self.Promotions["Race"]
			newUnit1 = initUnit(Unit["Hill Giant"], iX, iY, iNoAI, iNorth)
			newUnit1.setHasPromotion(Promo["Hidden Nationality"], True)
			newUnit1.setHasPromotion(Race["Undead"], False)

			if newUnit1.getRace() != -1:
				newUnit1.setHasPromotion(newUnit1.getRace(), False)
			newUnit1.setHasPromotion(Race["Giantkin"], True)
			newUnit1.setName("Larry")
			newUnit2 = initUnit(Unit["Hill Giant"], iX, iY, iNoAI, iNorth)
			newUnit2.setHasPromotion(Promo["Hidden Nationality"], True)
			newUnit2.setHasPromotion(Race["Undead"], False)
			if newUnit2.getRace() != -1:
				newUnit2.setHasPromotion(newUnit2.getRace(), False)
			newUnit2.setHasPromotion(Race["Giantkin"], True)
			newUnit2.setName("Curly")

			newUnit3 = initUnit(Unit["Hill Giant"], iX, iY, iNoAI, iNorth)
			newUnit3.setHasPromotion(Promo["Hidden Nationality"], True)
			newUnit3.setHasPromotion(Race["Undead"], False)
			if newUnit3.getRace() != -1:
				newUnit3.setHasPromotion(newUnit3.getRace(), False)
			newUnit3.setHasPromotion(Race["Giantkin"], True)
			newUnit3.setName("Moe")

		#elif iBuildingType == Building["Catacomb Libralus"]:
		#	if iStatus == Status["Important"] and not hasTrait(Trait["Arcane"]):
		#		triggerData(Event["Arcane"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		#elif iBuildingType == Building["Forbidden Palace"]:
		#	if iStatus == Status["Important"] and not hasTrait(Trait["Organized"]):
		#		triggerData(Event["Organized"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		#elif iBuildingType ==  Building["Altar - Anointed"]:
		#	if iStatus == Status["Important"] and not hasTrait(Trait["Magic Resistant"]):
		#		if not hasTrait(Trait["Ingenuity"]):
		#			triggerData(Event["Magic Resistant"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		elif iBuildingType == Building["Mercurian Gate"]:
			if not game.isCivEverActive(Civ["Mercurians"]):
				iMercurianPlayer = getOpenPlayer()
				pMercurians = gc.getPlayer(iMercurianPlayer)
				iTeam = pPlayer.getTeam()
				pPlot2 = findClearPlot(-1, pCity.plot())
				if (iMercurianPlayer != -1 and pPlot2 != -1):
					Unit 	 = self.Units["Mercurian"]
					Generic	 = self.Units["Generic"]
					initUnit = pMercurians.initUnit
					getUnit  = pPlot.getUnit
					iX = pPlot.getX(); iY = pPlot.getY();
					for i in xrange(pPlot.getNumUnits(), -1, -1):
						pUnit = getUnit(i)
						pUnit.setXY(pPlot2.getX(), pPlot2.getY(), True, True, True)
					game.addPlayerAdvanced(iMercurianPlayer, iTeam, self.Leaders["Basium"], Civ["Mercurians"],pPlayer.getID())
					basiumUnit = initUnit(self.Heroes["Basium"], iX, iY, iNoAI, iNorth)
					basiumUnit.setExperienceTimes100(2500, -1)
					initUnit(Generic["Settler"], iX, iY, iNoAI, iNorth)
					initUnit(Unit["Angel"], iX, iY, iNoAI, iNorth)
					initUnit(Unit["Angel"], iX, iY, iNoAI, iNorth)
					initUnit(Unit["Angel"], iX, iY, iNoAI, iNorth)
					initUnit(Unit["Angel"], iX, iY, iNoAI, iNorth)
					initUnit(Unit["Angel"], iX, iY, iNoAI, iNorth)
					initUnit(Unit["Angel"], iX, iY, iNoAI, iNorth)
					if pPlayer.isHuman():
						popupInfo = CyPopupInfo()
						popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
						popupInfo.setText(CyTranslator().getText("TXT_KEY_POPUP_CONTROL_MERCURIANS",()))
						popupInfo.setData1(player)
						popupInfo.setData2(iMercurianPlayer)
						popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_POPUP_YES", ()), "")
						popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_POPUP_NO", ()), "")
						popupInfo.setOnClickedPythonCallback("reassignPlayer")
						popupInfo.addPopup(player)
			else:
				if not game.isUnitClassMaxedOut(self.UnitClasses["Basium"], 0):
					if game.getNumCivActive(Civ["Mercurians"]) > 0:
						pMercurians  = getPlayer(game.getCivActivePlayer(Civ["Mercurians"], 0))
						pCapitalPlot = pMercurians.getCapitalCity()
						basiumUnit   = pMercurians.initUnit(iBasium, pCapitalPlot.getX(), pCapitalPlot.getY(), iNoAI, iNorth)
						basiumUnit.setExperienceTimes100(2500, -1)

		elif iBuildingType == Building["Tower of Elements"]:
			Promo	= self.Promotions["Effects"]
			Race	= self.Promotions["Race"]
			lList 	= ['UNIT_AIR_ELEMENTAL', 'UNIT_EARTH_ELEMENTAL', 'UNIT_FIRE_ELEMENTAL','UNIT_ICE_ELEMENTAL', 'UNIT_WATER_ELEMENTAL']
			iUnit 	= getInfoType(lList[randNum(len(lList), "Pick Elemental")-1])
			newUnit = pPlayer.initUnit(iUnit, iX, iY, iNoAI, iSouth)
			newUnit.setHasPromotion(Promo["Held"], True)
			CyInterface().addMessage(player,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_TOWER_OF_THE_ELEMENTS_SPAWN",()),'',1,gc.getUnitInfo(iUnit).getButton(),ColorTypes(8),iX,iY,True,True)
			apUnitList 	= PyPlayer(player).getUnitList()

			for pUnit in apUnitList:
				if pUnit.isHasPromotion(Race["Elemental"]):
					pUnit.setHasPromotion(Promo["Strong"], True)

		elif iBuildingType == Building["Tower of Necromancy"]:
			Promo	= self.Promotions["Effects"]
			Race	= self.Promotions["Race"]
			Summon	= self.Units["Summons"]
			Unit	= self.Units["Scions"]
			Veil	= self.Units["Veil"]
			apUnitList = PyPlayer(player).getUnitList()
			for pUnit in apUnitList:
				if pPlayer.getCivilizationType() != Civ["Scions"]:
					if pUnit.isHasPromotion(Race["Undead"]):
						pUnit.setHasPromotion(Promo["Strong"], True)
				else: # if Scions, limit the benefits (game balance)
					iUnitType = pUnit.getUnitType()
					if   iUnitType == Summon["Skeleton"]: 	   pUnit.setHasPromotion(Promo["Strong"], True)
					elif iUnitType == Unit["Bone Horde"]: 	   pUnit.setHasPromotion(Promo["Strong"], True)
					elif iUnitType == Veil["Diseased Corpse"]: pUnit.setHasPromotion(Promo["Strong"], True)

		elif iBuildingType == Building["Temple of the Gift"]:
			pCity.setNumRealBuilding( Building["Emperors Mark"], 0)

		elif iBuildingType == Building["Grand Menagerie"]:
			if pPlayer.isHuman():
				if not game.getWBMapScript():
					t = "TROPHY_FEAT_GRAND_MENAGERIE"
					if not game.isHasTrophy(t):
						game.changeTrophyValue(t, 1)


		elif iBuildingType == Building["Fisher Guild"]:
			pCity.setHasCorporation( self.Corporations["Fishermans"], True, True, False)
		elif iBuildingType == Building["Masquerade Gypsy Camp"]:
			pCity.setHasCorporation( self.Corporations["Masquerade"], True, True, False)
		elif iBuildingType == Building["Fabricaforma"]:
			pCity.setHasCorporation( self.Corporations["Fabricaforma"], True, True, False)
		elif iBuildingType == Building["Farmers Guild"]:
			pCity.setHasCorporation( self.Corporations["Farmers"], True, True, False)
		elif iBuildingType == Building["Stonefire Guild"]:
			pCity.setHasCorporation( self.Corporations["Stonefire"], True, True, False)
		elif iBuildingType == gc.getInfoTypeForString("BUILDING_MOKKAS_CAULDRON"):
			gc.getGame().setGlobalFlag(gc.getInfoTypeForString("FLAG_MOKKA_LOST"),False)
		CvAdvisorUtils.buildingBuiltFeats(pCity, iBuildingType)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onBuildingBuilt']:
			module.onBuildingBuilt(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_BUILDING):
			return
		CvUtil.pyPrint('%s was finished by Player %d Civilization %s'
			%(PyInfo.BuildingInfo(iBuildingType).getDescription(), pCity.getOwner(), gc.getPlayer(pCity.getOwner()).getCivilizationDescription(0)))

	def onProjectBuilt(self, argsList):
		'Project Completed'
		pCity, iProjectType = argsList

		gc = CyGlobalContext()
		cf				= self.cf
		getInfoType		= gc.getInfoTypeForString
		getPlayer 		= gc.getPlayer
		game 			= CyGame()
		map 			= CyMap()
		iNumPlots 		= map.numPlots()
		plotByIndex	 	= map.plotByIndex
		iPlayer 		= pCity.getOwner()
		pPlayer 		= getPlayer(iPlayer)
		iMaxPlayer 		= gc.getMAX_PLAYERS()
		eCiv			= pPlayer.getCivilizationType()
		isOption 		= game.isOption
		iTeam 			= pPlayer.getTeam()
		iOrcPlayer 		= gc.getORC_PLAYER()
		iAnimalPlayer 	= gc.getANIMAL_PLAYER()
		getTeam	 		= gc.getTeam
		iDemonPlayer 	= gc.getDEMON_PLAYER()
		randNum 		= game.getSorenRandNum
		Animal 			= self.Units["Animal"]
		Civ				= self.Civilizations
		Feature 		= self.Feature
		Generic 		= self.Promotions["Generic"]
		Leader			= self.Leaders
		Project			= self.Projects
		Promo			= self.Promotions["Effects"]
		Race  			= self.Promotions["Race"]
		Religion		= self.Religions
		Terrain 		= self.Terrain
		Unit			= self.Units["Generic"]
		UnitClass		= self.UnitClasses
		initUnit		= pPlayer.initUnit
		iNoPlayer 		= PlayerTypes.NO_PLAYER
		iNoAI			= UnitAITypes.NO_UNITAI
		iNorth 			= DirectionTypes.DIRECTION_NORTH
		iSouth 			= DirectionTypes.DIRECTION_SOUTH
		iRel			= pPlayer.getStateReligion()
		iX = pCity.getX(); iY = pCity.getY()

		if ((not game.isNetworkMultiPlayer()) and (iPlayer == game.getActivePlayer())) or not CyGame().GetWorldBuilderMode():
			popupInfo = CyPopupInfo()
			popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
			popupInfo.setData1(iProjectType)
			popupInfo.setData2(pCity.getID())
			popupInfo.setData3(2)
			popupInfo.setText(u"showWonderMovie")
			popupInfo.addPopup(iPlayer)

		if iProjectType == Project["Bane Divine"]:
			iCombatDisciple = self.UnitCombats["Disciple"]
			for iLoopPlayer in xrange(iMaxPlayer):
				pLoopPlayer = getPlayer(iLoopPlayer)
				if pLoopPlayer.isAlive() :
					apUnitList = PyPlayer(iLoopPlayer).getUnitList()
					for pUnit in apUnitList:
						if pUnit.getUnitCombatType() == iCombatDisciple:
							pUnit.kill(False, iPlayer)

		elif iProjectType == Project["Genesis"]:
			cf.genesis(iPlayer)

		elif iProjectType == Project["Glory Everlasting"]:
			iEvil = self.Alignments["Evil"]
			for iLoopPlayer in xrange(iMaxPlayer):
				pLoopPlayer = getPlayer(iLoopPlayer)
				player = PyPlayer(iLoopPlayer)
				if pLoopPlayer.isAlive():
					apUnitList = player.getUnitList()
					if pLoopPlayer.getTeam() != iTeam:
						if (pLoopPlayer.isBarbarian() or pLoopPlayer.getAlignment() == iEvil):
							for pUnit in apUnitList:
								hasPromo = pUnit.isHasPromotion
								if (hasPromo(Race["Demon"]) or hasPromo(Race["Undead"])):
									pUnit.kill(False, iPlayer)

		elif iProjectType == Project["Rites of Oghma"]:
			i = 7
			iWorldSize 	= map.getWorldSize()
			WorldSize 	= self.WorldSizes
			if   iWorldSize == WorldSize["Duel"]: i = i - 3
			elif iWorldSize == WorldSize["Tiny"]: i = i - 2
			elif iWorldSize == WorldSize["Small"]:i = i - 1
			elif iWorldSize == WorldSize["Large"]:i = i + 1
			elif iWorldSize == WorldSize["Huge"]: i = i + 3
			elif iWorldSize == WorldSize["Huger"]: i = i + 5
			addBonus('BONUS_MANA',i,'Art/Interface/Buttons/WorldBuilder/mana_button.dds')

		elif iProjectType == Project["Nature's Revolt"]:
			bPlayer 	  = getPlayer(iAnimalPlayer)
			py 			  = PyPlayer(iOrcPlayer)

			for pUnit in py.getUnitList():
				bValid = False
				iUC = pUnit.getUnitClassType()
				if   iUC == UnitClass["Worker"]:        iNewUnit = Animal["Elephant"];          bValid = True
				elif iUC == UnitClass["Scout"]:         iNewUnit = Animal["Sabretooth"];        bValid = True
				elif iUC == UnitClass["Warrior"]:       iNewUnit = Animal["Dire Wolf"];         bValid = True
				elif iUC == UnitClass["Hunter"]:        iNewUnit = Animal["Tyrant"];            bValid = True
				elif iUC == UnitClass["Axeman"]:        iNewUnit = Animal["Cave Bears"];         bValid = True
				elif iUC == UnitClass["Fawn"]:          iNewUnit = Animal["Roc"];               bValid = True
				elif iUC == UnitClass["Hill Giant"]:    iNewUnit = Animal["Red Drake"];         bValid = True
				elif iUC == UnitClass["Archer"]:        iNewUnit = Animal["Silverback"];        bValid = True
				elif iUC == UnitClass["Cyklop"]:        iNewUnit = Animal["Giant Spider"];      bValid = True
				elif iUC == UnitClass["Minotaur"]:      iNewUnit = Animal["Blood Boar"];        bValid = True
				elif iUC == UnitClass["Horseman"]:      iNewUnit = Animal["Giant Scorpion"];    bValid = True
				elif iUC == UnitClass["Frostling"]:     iNewUnit = Animal["White Drake"];       bValid = True

				if bValid:
					initAnimal = bPlayer.initUnit
					iX = pUnit.getX(); iY = pUnit.getY()
					newUnit = initAnimal(iNewUnit, iX, iY, iNoAI, iNorth)
					newUnit = initAnimal(iNewUnit, iX, iY, iNoAI, iNorth)
					newUnit = initAnimal(iNewUnit, iX, iY, iNoAI, iNorth)
					pUnit.kill(True, iNoPlayer)

			for iLoopPlayer in xrange(iMaxPlayer):
				pLoopPlayer = getPlayer(iLoopPlayer)
				if pLoopPlayer.isAlive():
					py = PyPlayer(iLoopPlayer)
					for pUnit in py.getUnitList():
						if pUnit.isAnimal():
							pUnit.setHasPromotion( Promo["Heroic Defense I"], True)
							pUnit.setHasPromotion( Promo["Heroic Defense II"], True)
							pUnit.setHasPromotion( Promo["Heroic Strength I"], True)
							pUnit.setHasPromotion( Promo["Heroic Strength II"], True)

		elif iProjectType == Project["Blood of the Phoenix"]:
			py = PyPlayer(iPlayer)
			apUnitList = py.getUnitList()
			for pUnit in apUnitList:
				if pUnit.isAlive() and pUnit.getUnitCombatType() != -1:
					if pUnit.getUnitClassType() != UnitClass["Fort Commander"]:
						pUnit.setHasPromotion( Promo["Immortal"], True)

		elif iProjectType == Project["Purge the Unfaithful"]:
			getBuildingInfo = gc.getBuildingInfo
			iNumReligions 	= gc.getNumReligionInfos()
			iNumBuildings 	= gc.getNumBuildingInfos()
			StateBelief = pPlayer.getStateReligion()
			for pyCity in PyPlayer(iPlayer).getCityList():
				pCity2 = pyCity.GetCy()
				iRnd = randNum(2, "Purge the Unfaithful Revolt")
				if iRel == Religion["Order"]:
					iRnd = iRnd - 1
				for iTarget in xrange(iNumReligions):
					if (StateBelief != iTarget and pCity2.isHasReligion(iTarget) and pCity2.isHolyCityByType(iTarget) == False):
						pCity2.setHasReligion(iTarget, False, True, True)
						iRnd = iRnd + 1
						for i in xrange(iNumBuildings):
							if getBuildingInfo(i).getPrereqReligion() == iTarget:
								pCity2.setNumRealBuilding(i, 0)
				if iRnd > 0:
					pCity2.setOccupationTimer(iRnd)

		elif iProjectType == Project["Birthright Regained"]:
			pPlayer.setFeatAccomplished(FeatTypes.FEAT_GLOBAL_SPELL, False)

		elif iProjectType == Project["Prepare Expedition"]:
			pPlayer.setFeatAccomplished(FeatTypes.FEAT_EXPEDITION_READY, True)

		elif iProjectType == Project["Samhain"]:
			Frostling = self.Units["Frostling"]
			iCount = game.countCivPlayersAlive() + int(game.getHandicapType()) - 5
			for i in xrange(iCount):
				addUnit( Frostling["Frostling"], iOrcPlayer)
				addUnit( Frostling["Frostling"], iOrcPlayer)
				addUnit( Frostling["Archer"], iOrcPlayer)
				addUnit( Frostling["Wolf Rider"], iOrcPlayer)
			mokkaunit=addUnit(self.Heroes["Mokka"], iOrcPlayer)
			if (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_MOKKA_LOST'))):
				mokkaunit.safeRemovePromotion(gc.getInfoTypeForString("PROMOTION_MOKKAS_CAULDRON"))
			gc.getGame().setGlobalFlag(gc.getInfoTypeForString('FLAG_MOKKA_LOST'),False)

		elif iProjectType == Project["The White Hand"]:
			Unit = self.Units["White Hand"]
			pCity.setHasReligion( Religion["White Hand"], True, True, True)
			newUnit1 = initUnit( Unit["Priest"], iX, iY, iNoAI, iSouth)
			newUnit1.setName("Dumannios")
			newUnit1.changeStrBoost(1)
			newUnit2 = initUnit( Unit["Priest"], iX, iY, iNoAI, iSouth)
			newUnit2.setName("Riuros")
			newUnit2.changeStrBoost(1)
			newUnit3 = initUnit( Unit["Priest"], iX, iY, iNoAI, iSouth)
			newUnit3.setName("Anagantios")
			newUnit3.changeStrBoost(1)

		elif iProjectType == Project["The Deepening"]:
			iTimer = 40 + (game.getGameSpeedType() * 20)
			for i in xrange(iNumPlots):
				pPlot = plotByIndex(i)
				bValid = False
				if pPlot.isWater() == False:
					if randNum(100, "The Deepening") < 25:
						iTerrain = pPlot.getTerrainType()
						if iTerrain == Terrain["Tundra"]:
							pPlot.setTempTerrainTypeFM( Terrain["Glacier"], randNum(iTimer, "Deepening Terrain Timer (Tundra)") + 10, False, False)
							bValid = True
# FF: Changed by Jean Elcard 14/01/2009 (speed tweak)
						elif iTerrain == Terrain["Taiga"]:
							pPlot.setTempTerrainTypeFM( Terrain["Tundra"], randNum(iTimer, "Deepening Terrain Timer (Taiga)") + 10, False, False)
							bValid = True
						elif iTerrain == Terrain["Grass"]:
							pPlot.setTempTerrainTypeFM( Terrain["Taiga"], randNum(iTimer, "Deepening Terrain Timer (Grass)") + 10, False, False)
							bValid = True
						elif iTerrain == Terrain["Plains"]:
							pPlot.setTempTerrainTypeFM( Terrain["Taiga"], randNum(iTimer, "Deepening Terrain Timer (Plains)") + 10, False, False)
							bValid = True
						elif iTerrain == Terrain["Desert"]:
							pPlot.setTempTerrainTypeFM( Terrain["Plains"], randNum(iTimer, "Deepening Terrain Timer (Desert)") + 10, False, False)
# FF: End Change
						if bValid:
							if randNum(750, "The Deepening, Blizzard Creation") < 10:
								pPlot.setFeatureType(Feature["Blizzard"], -1)

		elif iProjectType == Project["Stir From Slumber"]:
			initUnit(self.Heroes["Drifa"], iX, iY, iNoAI, iSouth)
			if pPlayer.getLeaderType() == self.Leaders["Raitlor"]:
				if not gc.isNoCrash():
					pPlayer.setHasTrait(self.Traits["Ice Touched"], True,-1,True,True)
				else:
					pPlayer.setHasTrait(self.Traits["Ice Touched"], True)
				
		elif iProjectType == Project["The Draw"]:
			pPlayer.changeNoDiplomacyWithEnemies(1)
			pPlayer.setHasFlag(gc.getDefineINT("FLAG_DRAW"),True)
			iTeam = pPlayer.getTeam()
			pTeam = getTeam(iTeam)
			for iLoopTeam in xrange(gc.getMAX_TEAMS()):
				if iLoopTeam != iTeam:
					if iLoopTeam != getPlayer(iOrcPlayer).getTeam() and iLoopTeam != getPlayer(iAnimalPlayer).getTeam() and iLoopTeam != getPlayer(iDemonPlayer).getTeam():
						eLoopTeam = getTeam(iLoopTeam)
						if eLoopTeam.isAlive():
							if not eLoopTeam.isAVassal():
								pTeam.declareWar(iLoopTeam, False, WarPlanTypes.WARPLAN_LIMITED)
			py = PyPlayer(iPlayer)
			for pUnit in py.getUnitList():
				iDmg = pUnit.getDamage() * 2
				if iDmg > 99:
					iDmg = 99
				if iDmg < 50:
					iDmg = 50
				pUnit.setDamage(iDmg, iPlayer)
			for pyCity in PyPlayer(iPlayer).getCityList():
				pCity = pyCity.GetCy()
				iPop = int(pCity.getPopulation() / 2)
				if iPop < 1:
					iPop = 1
				pCity.setPopulation(iPop)

		elif iProjectType == Project["Ascension"]:
			Hero = self.Heroes
			if eCiv == Civ["Illians"]:
				for iPlot in xrange(iNumPlots):
					pAuricPlot = plotByIndex(iPlot)
					for iUnit in xrange(pAuricPlot.getNumUnits()):
						pAuric = pAuricPlot.getUnit(iUnit)
						iAuric = 0
						if pAuric.getUnitType() == Hero["Auric"]:
							newUnit = initUnit( Hero["Auric Ascended"], pAuric.getX(), pAuric.getY(), iNoAI, iSouth)
							newUnit.convert(pAuric)
							iAuric = 1
							break
						elif pAuric.getUnitType() == Hero["Auric Winter"]:
							newUnit = initUnit( Hero["Auric Ascended"], pAuric.getX(), pAuric.getY(), iNoAI, iSouth)
							newUnit.convert(pAuric)
							iAuric = 1
							break

			for iLoopPlayer in xrange(iMaxPlayer):
				pLoopPlayer = getPlayer(iLoopPlayer)
				if pLoopPlayer.isAlive():
					if not pLoopPlayer.isBarbarian():
						if pLoopPlayer.getTeam() != pPlayer.getTeam():
							if pLoopPlayer.getStateReligion() == Religion["White Hand"]:
								getTeam(pLoopPlayer.getTeam()).setVassal(pPlayer.getTeam(), True, False)
			if pPlayer.isHuman():
				t = "TROPHY_FEAT_ASCENSION"
				if not game.isHasTrophy(t):
					game.changeTrophyValue(t, 1)
			if not game.getWBMapScript():
				iBestPlayer = -1
				iBestValue = 0
				getRank = game.getPlayerRank
				for iLoopPlayer in xrange(iMaxPlayer):
					pLoopPlayer = getPlayer(iLoopPlayer)
					if pLoopPlayer.isAlive():
						if not pLoopPlayer.isBarbarian():
							if pLoopPlayer.getTeam() != pPlayer.getTeam():
								if not pLoopPlayer.getStateReligion() == Religion["White Hand"]:
									iValue = randNum(500, "Ascension")
									if pLoopPlayer.isHuman():
										iValue += 2000
									iValue += (20 - getRank(iLoopPlayer)) * 50
									if iValue > iBestValue:
										iBestValue = iValue
										iBestPlayer = iLoopPlayer
				if iBestPlayer != -1:
					Equipment = self.Promotions["Equipment"]
					Item = self.Units["Equipment"]
					pBestPlayer = getPlayer(iBestPlayer)
					pBestCity = pBestPlayer.getCapitalCity()
					if pBestPlayer.isHuman():
						popupInfo	= CyPopupInfo()
						popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
						popupInfo.setOnClickedPythonCallback("passToModNetMessage")
						popupInfo.setData1(iBestPlayer)
						popupInfo.setData3(102) # onModNetMessage id
						popupInfo.setText(CyTranslator().getText("TXT_KEY_EVENT_GODSLAYER", ()))
						popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_EVENT_CONTINUE", ()),"")
						popupInfo.addPopup(iBestPlayer)
					else:
						containerUnit = -1
						pPlot = pBestCity.plot()
						getUnit = pPlot.getUnit
						for i in xrange(pPlot.getNumUnits()):
							if getUnit(i).getUnitType() == Item["Container"]:
								containerUnit = getUnit(i)
						if containerUnit == -1:
							containerUnit = getPlayer(iOrcPlayer).initUnit(Item["Container"], pPlot.getX(), pPlot.getY(), iNoAI, iSouth)
						containerUnit.setHasPromotion( Equipment["Godslayer"], True)


		elif iProjectType == Project["Pax Diabolis"]:
			pCity.setNumRealBuilding( self.Buildings["Pax Diabolis"], 1)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onProjectBuilt']:
			module.onProjectBuilt(self, argsList)

		## Modular Python End
		## *******************


	def onSelectionGroupPushMission(self, argsList):
		'selection group mission'
		eOwner = argsList[0]
		eMission = argsList[1]
		iNumUnits = argsList[2]
		listUnitIds = argsList[3]

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onSelectionGroupPushMission']:
			module.onSelectionGroupPushMission(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_PUSH_MISSION):
			return
		##if pHeadUnit:
		CvUtil.pyPrint("Selection Group pushed mission %d" %(eMission))

	def onUnitMove(self, argsList):
		'unit move'
		pPlot,pUnit,pOldPlot = argsList
		player = PyPlayer(pUnit.getOwner())
		unitInfo = PyInfo.UnitInfo(pUnit.getUnitType())
		randNum 		= game.getSorenRandNum
		
				## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitMove']:
			module.onUnitMove(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_MOVEMENT):
			return
		if player and unitInfo:
			CvUtil.pyPrint('Player %d Civilization %s unit %s is moving to %d, %d'
				%(player.getID(), player.getCivilizationName(), unitInfo.getDescription(),
				pUnit.getX(), pUnit.getY()))

	def onUnitSetXY(self, argsList):
		'units xy coords set manually'
		pPlot,pUnit = argsList
		player = PyPlayer(pUnit.getOwner())
		unitInfo = PyInfo.UnitInfo(pUnit.getUnitType())

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitSetXY']:
			module.onUnitSetXY(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_MOVEMENT):
			return

	def onUnitCreated(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Unit Completed'
		pUnit = argsList[0]
		self.verifyLoaded()
		gc 					= CyGlobalContext()
		getInfoType			= gc.getInfoTypeForString
		cf					= self.cf
		game 				= CyGame()
		player 				= PyPlayer(pUnit.getOwner())
		getPlayer 			= gc.getPlayer
		pPlayer 			= getPlayer(pUnit.getOwner())
		Civ					= self.Civilizations
		Promo				= self.Promotions["Effects"]
		Generic				= self.Promotions["Generic"]
		Race				= self.Promotions["Race"]
		Equipment			= self.Promotions["Equipment"]
		UnitCombat			= self.UnitCombats
		Tech				= self.Techs
		Mana				= self.Mana
		Bannor				= self.Units["Bannor"]
		Mechanos			= self.Units["Mechanos"]
		ScorpClan			= self.Units["Scorpion Clan"]
		Summon 				= self.Units["Summons"]
		Scions 				= self.Units["Scions"]
		Veil 				= self.Units["Veil"]
		setPromo 			= pUnit.setHasPromotion
		hasTrait 			= pPlayer.hasTrait
		Trait				= self.Traits
		iUnitType 			= pUnit.getUnitType()
		iUnitCombat 		= pUnit.getUnitCombatType()
		initUnit 			= pPlayer.initUnit
		getNumAvailBonuses 	= pPlayer.getNumAvailableBonuses
		getTeam 			= gc.getTeam
		hasPromo 			= pUnit.isHasPromotion
		randNum 			= game.getSorenRandNum
		iNoAI				= UnitAITypes.NO_UNITAI
		iSouth 				= DirectionTypes.DIRECTION_SOUTH
		pPlot 				= pUnit.plot()
		iX = pPlot.getX(); iY = pPlot.getY()

		if game.getAIAutoPlay() == 0:
			if (pUnit.isImage()):
				activePlayer = getPlayer(game.getActivePlayer())
				sPlayerName = player.getName()
				sUnitName = pUnit.getName()
				sQuote = pUnit.getQuote()
				if getTeam(pUnit.getTeam()).isHasMet(activePlayer.getTeam()):
					sPopupText = CyTranslator().getText('TXT_KEY_MISC_UNIT_POPUP',(sPlayerName, sUnitName, sQuote))
				else:
					sPopupText = CyTranslator().getText('TXT_KEY_MISC_UNIT_POPUP_UNKNOWN',(sUnitName, sQuote))
				addPopup(sPopupText, str(pUnit.getImage()))

		if hasTrait(Trait["Defender"]):
			if pUnit.getUnitCombatType() == UnitCombat["Worker"]:
				setPromo(Generic["Hardy I"], True)

		if hasTrait(Trait["Instructor"]):
			if iUnitType == Bannor["Demagog"]:
				pUnit.changeFreePromotionPick(1)
				
		if getInfoType("MODULE_EMERGENT_LEADERS")!=-1 and hasTrait(getInfoType("TRAIT_INCORPOREAL")):
			if iUnitCombat==getInfoType("UNITCOMBAT_MOUNTED") or pUnit.isSecondaryUnitCombat(getInfoType("UNITCOMBAT_MOUNTED")):
				setPromo(getInfoType("PROMOTION_ILLUSION"),True)

		if hasTrait(Trait["Spiderkin"]):
			pNest = pPlayer.getCapitalCity()
			iNestPop = pNest.getPopulation()
			spiderUnits = [getInfoType('UNIT_BABY_SPIDER'), getInfoType('UNIT_SPIDER'), getInfoType('UNIT_GIANT_SPIDER'), getInfoType('UNIT_NESTING_SPIDER'), getInfoType('UNIT_MOTHER_SPIDER')]
			if iNestPop >= 15 and pUnit.getUnitType() not in spiderUnits: setPromo(Promo["Spiderkin"], True)

		if iUnitType == ScorpClan["Whelp"]:
			GoblinChoice = [(ScorpClan["Goblin"], 10)]

			if pPlot.getNumUnits() > 5:							GoblinChoice = [(ScorpClan["Lord"], 25)]
			if pPlayer.isHasTech( Tech["Bowyers"]):				GoblinChoice = [(ScorpClan["Sapper"], 25), (ScorpClan["Archer"], 10)]
			elif pPlayer.isHasTech( Tech["Archery"]): 			GoblinChoice = [(ScorpClan["Archer"], 25)]
			if pPlayer.isHasTech( Tech["Stirrups"]):			GoblinChoice = [(ScorpClan["Wolf Archer"], 25), (ScorpClan["Wolf Rider"], 10)]
			elif pPlayer.isHasTech( Tech["Horseback Riding"]):	GoblinChoice = [(ScorpClan["Wolf Rider"], 25)]
			if pPlayer.isHasTech( Tech["Construction"]):		GoblinChoice = [(ScorpClan["Chariot"], 25)]

			getGoblin = wchoice( GoblinChoice, 'Goblin Whelp Upgrade' )
			newUnit = initUnit(getGoblin(), iX, iY, iNoAI, iSouth)
			newUnit.convert(pUnit)
			pUnit = newUnit

		if pUnit.getUnitCombatType() == UnitCombat["Adept"]:
			iNum = getNumAvailBonuses( Mana["Air"])
			eCiv = pPlayer.getCivilizationType()
			if iNum > 1:
				setPromo(Generic["Air I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Air II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Air III"], True)
			iNum = getNumAvailBonuses( Mana["Body"])
			if eCiv in [Civ["Scions"],Civ["D'Tesh"]]:
				if iNum > 1:
					setPromo(Generic["Corpus I"], True)
					if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
						setPromo(Generic["Corpus II"], True)
						if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
							setPromo(Generic["Corpus III"], True)
			else:
				if iNum > 1:
					setPromo(Generic["Body I"], True)
					if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
						setPromo(Generic["Body II"], True)
						if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
							setPromo(Generic["Body III"], True)
			iNum = getNumAvailBonuses( Mana["Chaos"])
			if iNum > 1:
				setPromo(Generic["Chaos I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Chaos II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Chaos III"], True)
			iNum = getNumAvailBonuses( Mana["Death"])
			if iNum > 1:
				setPromo(Generic["Death I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Death II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Death III"], True)
			iNum = getNumAvailBonuses( Mana["Earth"])
			if iNum > 1:
				setPromo(Generic["Earth I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Earth II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Earth III"], True)
			iNum = getNumAvailBonuses( Mana["Enchantment"])
			if iNum > 1:
				setPromo(Generic["Enchantment I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Enchantment II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Enchantment III"], True)
			iNum = getNumAvailBonuses( Mana["Entropy"])
			if iNum > 1:
				setPromo(Generic["Entropy I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Entropy II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Entropy III"], True)
			iNum = getNumAvailBonuses( Mana["Fire"])
			if iNum > 1:
				setPromo(Generic["Fire I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Fire II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Fire III"], True)
			iNum = getNumAvailBonuses( Mana["Ice"])
			if iNum > 1:
				setPromo(Generic["Ice I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Ice II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Ice III"], True)
			iNum = getNumAvailBonuses( Mana["Law"])
			if iNum > 1:
				setPromo(Generic["Law I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Law II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Law III"], True)
			iNum = getNumAvailBonuses( Mana["Life"])
			if iNum > 1:
				setPromo(Generic["Life I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Life II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Life III"], True)
			iNum = getNumAvailBonuses( Mana["Metamagic"])
			if iNum > 1:
				setPromo(Generic["Metamagic I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Metamagic II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Metamagic III"], True)
			iNum = getNumAvailBonuses( Mana["Mind"])
			if iNum > 1:
				setPromo(Generic["Mind I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Mind II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Mind III"], True)
			iNum = getNumAvailBonuses( Mana["Nature"])
			if iNum > 1:
				setPromo(Generic["Nature I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Nature II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Nature III"], True)
			iNum = getNumAvailBonuses( Mana["Shadow"])
			if iNum > 1:
				setPromo(Generic["Shadow I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Shadow II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Shadow III"], True)
			iNum = getNumAvailBonuses( Mana["Spirit"])
			if iNum > 1:
				setPromo(Generic["Spirit I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Spirit II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Spirit III"], True)
			iNum = getNumAvailBonuses( Mana["Sun"])
			if iNum > 1:
				setPromo(Generic["Sun I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Sun II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Sun III"], True)
			iNum = getNumAvailBonuses( Mana["Water"])
			if iNum > 1:
				setPromo(Generic["Water I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Water II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Water III"], True)
			iNum = getNumAvailBonuses( Mana["Creation"])
			if iNum > 1:
				setPromo(Generic["Creation I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Creation II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Creation III"], True)
			iNum = getNumAvailBonuses( Mana["Force"])
			if iNum > 1:
				setPromo(Generic["Force I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Force II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Force III"], True)
			iNum = getNumAvailBonuses( Mana["Dimensional"])
			if iNum > 1:
				setPromo(Generic["Dimensional I"], True)
				if (iNum > 2 and hasPromo( Promo["Channeling II"] )):
					setPromo(Generic["Dimensional II"], True)
					if (iNum > 3 and hasPromo( Promo["Channeling III"] )):
						setPromo(Generic["Dimensional III"], True)

		if hasPromo(Race["Elemental"]):
			if pPlayer.getNumBuilding(self.Buildings["Tower of Elements"]) > 0:
				setPromo(Promo["Strong"], True)

		if hasPromo(Race["Undead"]):
			if pPlayer.getNumBuilding(self.Buildings["Tower of Necromancy"]) > 0:
				if pPlayer.getCivilizationType() != Civ["Scions"]:
					setPromo( Promo["Strong"], True)
				else: #scions specifics
					if   iUnitType == Summon["Skeleton"]:       setPromo( Promo["Strong"], True)
					elif iUnitType == Summon["Spectre"]:        setPromo( Promo["Strong"], True)
					elif iUnitType == Summon["Wraith"]:         setPromo( Promo["Strong"], True)
					elif iUnitType == Veil["Diseased Corpse"]:  setPromo( Promo["Strong"], True)
					elif iUnitType == Scions["Bone Horde"]:     setPromo( Promo["Strong"], True)

		if pUnit.isAlive() and pUnit.baseCombatStr()>0:
			bAdded=False
			bCheckedAtWar=False
			bAtWar=False
			if (not bAdded) and (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_CAPRIA'))):
				if (not bCheckedAtWar):
					bCheckedAtWar=True
					for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
						pLoopPlayer=gc.getPlayer(iLoopPlayer)
						
						if gc.getTeam(pPlayer.getTeam()).isAtWar(pLoopPlayer.getTeam()):
							bAtWar=True
				if bAtWar:
					bAdded=True
					if randNum(100, "Aspect") < 5:
						setPromo(gc.getInfoTypeForString('PROMOTION_ASPECT_OF_WAR_CAPRIA'),True)
						game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_CAPRIA'),True)
			if (not bAdded) and (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_UNKNOWN_2'))):
				if (not bCheckedAtWar):
					bCheckedAtWar=True
					for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
						pLoopPlayer=gc.getPlayer(iLoopPlayer)
						
						if gc.getTeam(pPlayer.getTeam()).isAtWar(pLoopPlayer.getTeam()):
							bAtWar=True
				if bAtWar:
					bAdded=True
					if randNum(100, "Aspect") < 5:
						setPromo(gc.getInfoTypeForString('PROMOTION_ASPECT_OF_WAR_UNKNOWN_2'),True)
						game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_UNKNOWN_2'),True)
			if (not bAdded) and (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_UNKNOWN_1'))):
				if (not bCheckedAtWar):
					bCheckedAtWar=True
					for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
						pLoopPlayer=gc.getPlayer(iLoopPlayer)
						
						if gc.getTeam(pPlayer.getTeam()).isAtWar(pLoopPlayer.getTeam()):
							bAtWar=True
				if bAtWar:
					bAdded=True
					if randNum(100, "Aspect") < 5:
						setPromo(gc.getInfoTypeForString('PROMOTION_ASPECT_OF_WAR_UNKNOWN_1'),True)
						game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_UNKNOWN_1'),True)
			if (not bAdded) and (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_ORTHUS'))):
				if (not bCheckedAtWar):
					bCheckedAtWar=True
					for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
						pLoopPlayer=gc.getPlayer(iLoopPlayer)
						
						if gc.getTeam(pPlayer.getTeam()).isAtWar(pLoopPlayer.getTeam()):
							bAtWar=True
				if bAtWar:
					bAdded=True
					if randNum(100, "Aspect") < 5:
						setPromo(gc.getInfoTypeForString('PROMOTION_ASPECT_OF_WAR_ORTHUS'),True)
						game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_ORTHUS'),True)
						
			if (not bAdded) and (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_ARAK'))):
				if (not bCheckedAtWar):
					bCheckedAtWar=True
					for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
						pLoopPlayer=gc.getPlayer(iLoopPlayer)
						
						if gc.getTeam(pPlayer.getTeam()).isAtWar(pLoopPlayer.getTeam()):
							bAtWar=True
				if bAtWar:
					bAdded=True
					if randNum(100, "Aspect") < 5:
						setPromo(gc.getInfoTypeForString('PROMOTION_ASPECT_OF_WAR_ARAK'),True)
						game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_ARAK'),True)
						
			if (not bAdded) and (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_MAGNADINE'))):
				if (not bCheckedAtWar):
					bCheckedAtWar=True
					for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
						pLoopPlayer=gc.getPlayer(iLoopPlayer)
						
						if gc.getTeam(pPlayer.getTeam()).isAtWar(pLoopPlayer.getTeam()):
							bAtWar=True
				if bAtWar:
					bAdded=True
					if randNum(100, "Aspect") < 5:
						setPromo(gc.getInfoTypeForString('PROMOTION_ASPECT_OF_WAR_MAGNADINE'),True)
						game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_MAGNADINE'),True)
						
			if (not bAdded) and (not pPlayer.isHasFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_MAHON'))):
				if (not bCheckedAtWar):
					bCheckedAtWar=True
					for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
						pLoopPlayer=gc.getPlayer(iLoopPlayer)
						
						if gc.getTeam(pPlayer.getTeam()).isAtWar(pLoopPlayer.getTeam()):
							bAtWar=True
				if bAtWar:
					bAdded=True
					if randNum(100, "Aspect") < 5:
						setPromo(gc.getInfoTypeForString('PROMOTION_ASPECT_OF_WAR_MAHON'),True)
						game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_MAHON'),True)
#		# mekara start - Handles wipes of XP from units converted to sluga
#		if pPlayer.getCivilizationType() == gc.getInfoTypeForString('CIVILIZATION_MEKARA'):
#			if iUnitType == gc.getInfoTypeForString('UNIT_SLUGA') or iUnitType == gc.getInfoTypeForString('UNIT_BATTLE_SLUGA'):
#				for iPromotion in xrange(gc.getNumPromotionInfos()):
#off					if pUnit.isHasPromotion(iPromotion) and not pUnit.canAcquirePromotion(iPromotion):
#for						CvUtil.pyPrint('Mekara promotion event: %s - %s' %(gc.getPromotionInfo(iPromotion).getDescription(), pUnit.getName(),))
#now						pUnit.setHasPromotion(iPromotion,False)
#				pUnit.setExperience(0.,0)	
			#	newUnit = pPlayer.initUnit(iUnitType, pUnit.getX(), pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
			#	pUnit.kill(True, 0)

		if pUnit.getUnitCombatType()==getInfoType("UNITCOMBAT_MOUNTED") or pUnit.isSecondaryUnitCombat(getInfoType("UNITCOMBAT_MOUNTED")):
			CvUtil.pyPrint ("hello")
			if (gc.getUnitInfo(pUnit.getUnitType()).getPrereqOrBonuses(0)==getInfoType("BONUS_HORSE")):
				CvUtil.pyPrint ("work")
				bHasDefaultMount=False
				for promo in ["PROMOTION_HORSE","PROMOTION_NIGHTMARE","PROMOTION_HYAPON","PROMOTION_CAMEL"]:
					if gc.getUnitInfo(pUnit.getUnitType()).getFreePromotions(getInfoType(promo)):
						bHasDefaultMount=True
						break
				if (not bHasDefaultMount):
					if pPlayer.hasBonus(getInfoType("BONUS_HORSE")):
						pUnit.setHasPromotion(getInfoType("PROMOTION_HORSE"),True)
					elif pPlayer.hasBonus(getInfoType("BONUS_NIGHTMARE")):
						pUnit.setHasPromotion(getInfoType("PROMOTION_NIGHTMARE"),True)
					elif pPlayer.hasBonus(getInfoType("BONUS_HYAPON")):
						pUnit.setHasPromotion(getInfoType("PROMOTION_HYAPON"),True)
					elif pPlayer.hasBonus(getInfoType("BONUS_CAMEL")) and pPlayer.getCivilizationType()==getInfoType("CIVILIZATION_MALAKIM"):
						pUnit.setHasPromotion(getInfoType("PROMOTION_CAMEL"),True)
		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitCreated']:
			module.onUnitCreated(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_UNITBUILD):
			return

	def onUnitBuilt(self, argsList):
		'Unit Completed'
		pCity = argsList[0]
		pUnit = argsList[1]

		gc = CyGlobalContext()
		cf			= self.cf
		getInfoType	= gc.getInfoTypeForString
		game 		= CyGame()
		map 		= CyMap()
		player 		= PyPlayer(pCity.getOwner())
		getPlayer	= gc.getPlayer
		pPlayer 	= getPlayer(pUnit.getOwner())
		iFreeProm 	= pUnit.getFreePromotionPick()
		getNumB 	= pCity.getNumBuilding
		getNumAvailBonuses = pPlayer.getNumAvailableBonuses
		iUnitType = pUnit.getUnitType()
		iCombatType = pUnit.getUnitCombatType()
		setPromo 	= pUnit.setHasPromotion
		randNum		= game.getSorenRandNum
		hasTrait 			= pPlayer.hasTrait

		Promo	 	= self.Promotions["Effects"]
		Generic	 	= self.Promotions["Generic"]
		Race		= self.Promotions["Race"]
		Leader		= self.Leaders
		Trait		= self.Traits
		Mana 		= self.Mana
		Building 	= self.Buildings
		Civ			= self.Civilizations
		Veil		= self.Units["Veil"]
		UnitCombat	= self.UnitCombats
		Hero		= self.Heroes
		Terrain		= self.Terrain
		Feature		= self.Feature
		if pUnit.isAlive():
			pPlot = pCity.plot()
			getUnit = pPlot.getUnit
			countangel=0
			countdemon=0
			countslyph=0
			for i in xrange(pPlot.getNumUnits()):
				if getUnit(i).isHasPromotion(getInfoType("PROMOTION_ANGEL")):
					countangel=countangel+1
				if getUnit(i).isHasPromotion(getInfoType("PROMOTION_SLYPH")):
					countslyph=countslyph+1
				if getUnit(i).isHasPromotion(getInfoType("PROMOTION_DEMON")):
					countdemon=countdemon+1
			if randNum(100,"Aasimar")<countangel:
				pUnit.setHasPromotion(getInfoType("PROMOTION_AASIMAR"),True)
			if randNum(100,"Slyph")<countslyph:
				pUnit.setHasPromotion(getInfoType("PROMOTION_SLYPH_BLOOD"),True)
			if randNum(100,"Cambion")<countdemon:
				pUnit.setHasPromotion(getInfoType("PROMOTION_CAMBION"),True)
			
		if iUnitType == Veil["Beast of Agares"]:
			if pCity.getCivilizationType() != Civ["Infernal"]:
				iPop = pCity.getPopulation() - 4
				if iPop <= 1:
					iPop = 1
				pCity.setPopulation(iPop)
				pCity.setOccupationTimer(4)

		if getNumB( Building["Chancel of Guardians"]) > 0:
			if randNum(100, "Chancel of Guardians") < 20:
				setPromo( Generic["Defensive"], True)

	#	if hasTrait(Trait["Instructor3"]):
	#		if pUnit.getUnitCombatType() != UnitCombat["Siege"] and pUnit.getUnitCombatType() != UnitCombat["Naval"]:
	#			pUnit.changeFreePromotionPick(3)
	#	elif hasTrait(Trait["Instructor2"]):
	#		if pUnit.getUnitCombatType() != UnitCombat["Siege"] and pUnit.getUnitCombatType() != UnitCombat["Naval"]:
	#			pUnit.changeFreePromotionPick(2)
		if hasTrait(Trait["Instructor"]):
			if pUnit.getUnitCombatType() != UnitCombat["Siege"] and pUnit.getUnitCombatType() != UnitCombat["Naval"]:
				pUnit.changeFreePromotionPick(1)
		#*************************************************************************************************#
		#** Amurite Civilization - free promos                                                          **#
		#*************************************************************************************************#
		if (getNumB( Building["Wizards Hall"]) > 0 or getNumB(Building["Cave of Ancestors"]) > 0 or getNumB( Building["School of Govannon"]) > 0) and (iCombatType == gc.getInfoTypeForString("UNITCOMBAT_ROGUE") or iCombatType == gc.getInfoTypeForString("UNITCOMBAT_DEFENSIVE_MELEE") or iCombatType == UnitCombat["Melee"] or iCombatType == UnitCombat["Archer"] or iCombatType == UnitCombat["Mounted"] or iCombatType == UnitCombat["Recon"] or iCombatType == UnitCombat["Adept"] or iCombatType == UnitCombat["Disciple"]):
			# Count the 21 mana types
			iAirNum = getNumAvailBonuses( Mana["Air"])
			iBodNum = getNumAvailBonuses( Mana["Body"])
			iChaNum = getNumAvailBonuses( Mana["Chaos"])
			iCreNum = getNumAvailBonuses( Mana["Creation"])
			iDeaNum = getNumAvailBonuses( Mana["Death"])
			iDimNum = getNumAvailBonuses( Mana["Dimensional"])
			iEarNum = getNumAvailBonuses( Mana["Earth"])
			iEncNum = getNumAvailBonuses( Mana["Enchantment"])
			iEntNum = getNumAvailBonuses( Mana["Entropy"])
			iFirNum = getNumAvailBonuses( Mana["Fire"])
			iForNum = getNumAvailBonuses( Mana["Force"])
			iIceNum = getNumAvailBonuses( Mana["Ice"])
			iLawNum = getNumAvailBonuses( Mana["Law"])
			iLifNum = getNumAvailBonuses( Mana["Life"])
			iMetNum = getNumAvailBonuses( Mana["Metamagic"])
			iMinNum = getNumAvailBonuses( Mana["Mind"])
			iNatNum = getNumAvailBonuses( Mana["Nature"])
			iSpiNum = getNumAvailBonuses( Mana["Spirit"])
			iShaNum = getNumAvailBonuses( Mana["Shadow"])
			iSunNum = getNumAvailBonuses( Mana["Sun"])
			iWatNum = getNumAvailBonuses( Mana["Water"])
			if getNumB( Building["Wizards Hall"]) > 0 and getNumB(Building["Cave of Ancestors"]) == 0:
				lPromoList = []
				if iAirNum > 0:
					lPromoList = lPromoList + ['PROMOTION_AIR1']
				if iBodNum > 0:
					lPromoList = lPromoList + ['PROMOTION_BODY1']
				if iChaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_CHAOS1']
				if iCreNum > 0:
					lPromoList = lPromoList + ['PROMOTION_CREATION1']
				if iDeaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_DEATH1']
				if iDimNum > 0:
					lPromoList = lPromoList + ['PROMOTION_DIMENSIONAL1']
				if iEarNum > 0:
					lPromoList = lPromoList + ['PROMOTION_EARTH1']
				if iEncNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ENCHANTMENT1']
				if iEntNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ENTROPY1']
				if iFirNum > 0:
					lPromoList = lPromoList + ['PROMOTION_FIRE1']
				if iForNum > 0:
					lPromoList = lPromoList + ['PROMOTION_FORCE1']
				if iIceNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ICE1']
				if iLawNum > 0:
					lPromoList = lPromoList + ['PROMOTION_LAW1']
				if iLifNum > 0:
					lPromoList = lPromoList + ['PROMOTION_LIFE1']
				if iMetNum > 0:
					lPromoList = lPromoList + ['PROMOTION_METAMAGIC1']
				if iMinNum > 0:
					lPromoList = lPromoList + ['PROMOTION_MIND1']
				if iNatNum > 0:
					lPromoList = lPromoList + ['PROMOTION_NATURE1']
				if iShaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SHADOW1']
				if iSpiNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SPIRIT1']
				if iSunNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SUN1']
				if iWatNum > 0:
					lPromoList = lPromoList + ['PROMOTION_WATER1']
				if len(lPromoList) > 0:
					if randNum(100, "Spell Gain Check") < 20 + ((iAirNum + iBodNum + iChaNum + iCreNum + iDeaNum + iDimNum + iEarNum + iEncNum + iEntNum + iFirNum + iForNum + iIceNum + iLawNum + iLifNum + iMetNum + iMinNum + iNatNum + iShaNum + iSpiNum + iSunNum + iWatNum)*5):
						sPromo = lPromoList[randNum(len(lPromoList), "Pick Promotion")]
						setPromo(getInfoType(sPromo), True)

			elif getNumB( Building["Wizards Hall"]) > 0 and getNumB(Building["Cave of Ancestors"]) > 0:
				lPromoList = []
				if iAirNum > 0:
					lPromoList = lPromoList + ['PROMOTION_AIR1', 'PROMOTION_AIR2']
				if iBodNum > 0:
					lPromoList = lPromoList + ['PROMOTION_BODY1', 'PROMOTION_BODY2']
				if iChaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_CHAOS1', 'PROMOTION_CHAOS2']
				if iCreNum > 0:
					lPromoList = lPromoList + ['PROMOTION_CREATION1', 'PROMOTION_CREATION2']
				if iDeaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_DEATH1', 'PROMOTION_DEATH2']
				if iDimNum > 0:
					lPromoList = lPromoList + ['PROMOTION_DIMENSIONAL1', 'PROMOTION_DIMENSIONAL2']
				if iEarNum > 0:
					lPromoList = lPromoList + ['PROMOTION_EARTH1', 'PROMOTION_EARTH2']
				if iEncNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ENCHANTMENT1', 'PROMOTION_ENCHANTMENT2']
				if iEntNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ENTROPY1', 'PROMOTION_ENTROPY2']
				if iFirNum > 0:
					lPromoList = lPromoList + ['PROMOTION_FIRE1', 'PROMOTION_FIRE2']
				if iForNum > 0:
					lPromoList = lPromoList + ['PROMOTION_FORCE1', 'PROMOTION_FORCE2']
				if iIceNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ICE1', 'PROMOTION_ICE2']
				if iLawNum > 0:
					lPromoList = lPromoList + ['PROMOTION_LAW1', 'PROMOTION_LAW2']
				if iLifNum > 0:
					lPromoList = lPromoList + ['PROMOTION_LIFE1', 'PROMOTION_LIFE2']
				if iMetNum > 0:
					lPromoList = lPromoList + ['PROMOTION_METAMAGIC1', 'PROMOTION_METAMAGIC2']
				if iMinNum > 0:
					lPromoList = lPromoList + ['PROMOTION_MIND1', 'PROMOTION_MIND2']
				if iNatNum > 0:
					lPromoList = lPromoList + ['PROMOTION_NATURE1', 'PROMOTION_NATURE2']
				if iShaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SHADOW1', 'PROMOTION_SHADOW2']
				if iSpiNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SPIRIT1', 'PROMOTION_SPIRIT2']
				if iSunNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SUN1', 'PROMOTION_SUN2']
				if iWatNum > 0:
					lPromoList = lPromoList + ['PROMOTION_WATER1', 'PROMOTION_WATER2']
				if len(lPromoList) > 0:
					if randNum(100, "Spell Gain Check") < 20 + ((iAirNum + iBodNum + iChaNum  + iCreNum + iDeaNum + iDimNum + iEarNum + iEncNum + iEntNum + iFirNum + iForNum + iIceNum + iLawNum + iLifNum + iMetNum + iMinNum + iNatNum + iShaNum + iSpiNum + iSunNum + iWatNum)*5):
						sPromo = lPromoList[randNum(len(lPromoList), "Pick Promotion")]
						setPromo(getInfoType(sPromo), True)

			if getNumB( Building["School of Govannon"]) > 0:
				lPromoList = []
				if iAirNum > 0:
					lPromoList = lPromoList + ['PROMOTION_AIR1', 'PROMOTION_AIR2', 'PROMOTION_AIR3']
				if iBodNum > 0:
					lPromoList = lPromoList + ['PROMOTION_BODY1', 'PROMOTION_BODY2', 'PROMOTION_BODY3']
				if iChaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_CHAOS1', 'PROMOTION_CHAOS2', 'PROMOTION_CHAOS3']
				if iCreNum > 0:
					lPromoList = lPromoList + ['PROMOTION_CREATION1', 'PROMOTION_CREATION2', 'PROMOTION_CREATION3']
				if iDeaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_DEATH1', 'PROMOTION_DEATH2', 'PROMOTION_DEATH3']
				if iDimNum > 0:
					lPromoList = lPromoList + ['PROMOTION_DIMENSIONAL1', 'PROMOTION_DIMENSIONAL2', 'PROMOTION_DIMENSIONAL3']
				if iEarNum > 0:
					lPromoList = lPromoList + ['PROMOTION_EARTH1', 'PROMOTION_EARTH2', 'PROMOTION_EARTH3']
				if iEncNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ENCHANTMENT1', 'PROMOTION_ENCHANTMENT2', 'PROMOTION_ENCHANTMENT3']
				if iEntNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ENTROPY1', 'PROMOTION_ENTROPY2', 'PROMOTION_ENTROPY3']
				if iFirNum > 0:
					lPromoList = lPromoList + ['PROMOTION_FIRE1', 'PROMOTION_FIRE2', 'PROMOTION_FIRE3']
				if iForNum > 0:
					lPromoList = lPromoList + ['PROMOTION_FORCE1', 'PROMOTION_FORCE2', 'PROMOTION_FORCE3']
				if iIceNum > 0:
					lPromoList = lPromoList + ['PROMOTION_ICE1', 'PROMOTION_ICE2', 'PROMOTION_ICE3']
				if iLawNum > 0:
					lPromoList = lPromoList + ['PROMOTION_LAW1', 'PROMOTION_LAW2', 'PROMOTION_LAW3']
				if iLifNum > 0:
					lPromoList = lPromoList + ['PROMOTION_LIFE1', 'PROMOTION_LIFE2', 'PROMOTION_LIFE3']
				if iMetNum > 0:
					lPromoList = lPromoList + ['PROMOTION_METAMAGIC1', 'PROMOTION_METAMAGIC2', 'PROMOTION_METAMAGIC3']
				if iMinNum > 0:
					lPromoList = lPromoList + ['PROMOTION_MIND1', 'PROMOTION_MIND2', 'PROMOTION_MIND3']
				if iNatNum > 0:
					lPromoList = lPromoList + ['PROMOTION_NATURE1', 'PROMOTION_NATURE2', 'PROMOTION_NATURE3']
				if iShaNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SHADOW1', 'PROMOTION_SHADOW2', 'PROMOTION_SHADOW3']
				if iSpiNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SPIRIT1', 'PROMOTION_SPIRIT2', 'PROMOTION_SPIRIT3']
				if iSunNum > 0:
					lPromoList = lPromoList + ['PROMOTION_SUN1', 'PROMOTION_SUN2', 'PROMOTION_SUN3']
				if iWatNum > 0:
					lPromoList = lPromoList + ['PROMOTION_WATER1', 'PROMOTION_WATER2', 'PROMOTION_WATER3']
				if len(lPromoList) > 0:
					if game.getSorenRandNum(100, "Spell Gain Check") < ((iAirNum + iBodNum + iChaNum + iCreNum + iDeaNum + iDimNum + iEarNum + iEncNum + iEntNum + iFirNum + iForNum + iIceNum + iLawNum + iLifNum + iMetNum + iMinNum + iNatNum + iShaNum + iSpiNum + iSunNum + iWatNum)*3):
						sPromo = lPromoList[randNum(len(lPromoList), "Pick Promotion")]
						setPromo(getInfoType(sPromo), True)

			if getNumB(Building["Cave of Ancestors"]) > 0 and iCombatType == UnitCombat["Adept"]:
				i = 0
				for iBonus in xrange(gc.getNumBonusInfos()):
					if gc.getBonusInfo(iBonus).getBonusClassType() == Mana["Mana Class"]:
						if pCity.hasBonus(iBonus):
							i = i + 1
				if i >= 1:
					pUnit.changeExperience(i, -1, False, False, False)
		#*************************************************************************************************#
		#** Amurite Civilization - free promos                                                      END **#
		#*************************************************************************************************#
		#*************************************************************************************************#
		#** Luchuirp Civilization - free promos                                                         **#
		#*************************************************************************************************#
		if pUnit.isHasPromotion( Race["Golem"]):
			if getNumB( Building["Blasting Workshop"]) > 0:
				setPromo( Generic["Fire II"], True)
			if getNumB( Building["Pallens Engine"]) > 0:
				setPromo( Generic["Perfect Sight"], True)
			if getNumB( Building["Adularia Chamber"]) > 0:
				setPromo( Promo["Hidden"], True)
		#*************************************************************************************************#
		#** Luchuirp Civilization - free promos                                                     END **#
		#*************************************************************************************************#

		if getNumB( Building["Asylum"]) > 0:
			if pUnit.isAlive():
				if isWorldUnitClass(pUnit.getUnitClassType()) == False:
					if game.getSorenRandNum(100, "Asylum Crazed Application") <= 10:
						setPromo( Generic["Crazed"], True)
						setPromo( Generic["Enraged"], True)

		if iUnitType == Hero["Acheron"]:
			pCity.setNumRealBuilding( Building["Dragons Hoard"], 1)
			iX = pCity.getX()
			iY = pCity.getY()
			setPromo( Promo["Acheron Leashed"], True)
			getPlot = map.plot
			for iiX,iiY in RANGE1:
				pPlot = getPlot(iX+iiX,iY+iiY)
				if (pPlot.getFeatureType() == Feature["Forest"] or pPlot.getFeatureType() == Feature["Jungle"]):
					pPlot.setFeatureType( Feature["Flames"], 0)

		if pUnit.isHasPromotion( Race["Dwarven"]):
			if getNumB( Building["Brewery"]) > 0:
				pUnit.changeExperience(2, -1, False, False, False)

		if pUnit.isHasPromotion( Race["Demon"]):
			if getNumB( Building["Demons Altar"]) > 0:
				pUnit.changeExperience(2, -1, False, False, False)

		if pUnit.getFreePromotionPick() < iFreeProm:
			pUnit.changeFreePromotionPick(iFreeProm - pUnit.getFreePromotionPick())

		if pPlayer.getCivilizationType() == Civ["Austrin"]:
			if iCombatType == UnitCombat["Naval"]:
				setPromo( Generic["Eastwinds"], True)

# Mekara Start - Makes sure sluga start without XP or promotions
#		if pPlayer.getCivilizationType() == Civ["Mekara Order"]:
#			if iUnitType == gc.getInfoTypeForString('UNIT_SLUGA') or iUnitType == gc.getInfoTypeForString('UNIT_BATTLE_SLUGA'):
#				newUnit = pPlayer.initUnit(iUnitType, pUnit.getX(), pUnit.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
#				pUnit.kill(True, 0)
#Disabled for now

		if iUnitType == gc.getInfoTypeForString("UNIT_KAHD"):
			if(hasTrait(gc.getInfoTypeForString("TRAIT_KAHD_MAMMON"))):
				pUnit.setHasPromotion(getInfoType('PROMOTION_MIND1'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_MIND2'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_MIND3'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_AMBITION'), True)
				pUnit.setHasPromotion(getInfoType('COMPELLING_JEWEL'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_HERO'), True)
			else:
				pUnit.setHasPromotion(getInfoType('PROMOTION_METAMAGIC1'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_METAMAGIC2'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_METAMAGIC3'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_MAGIC_RESISTANCE'), True)
				pUnit.setHasPromotion(getInfoType('PROMOTION_KAHD_REDEEMED'), True)
			

		CvAdvisorUtils.unitBuiltFeats(pCity, pUnit)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitBuilt']:
			module.onUnitBuilt(self, argsList)

		## Modular Python End
		## *******************


		if (not self.__LOG_UNITBUILD):
			return
		CvUtil.pyPrint('%s was finished by Player %d Civilization %s'
			%(PyInfo.UnitInfo(pUnit.getUnitType()).getDescription(), player.getID(), player.getCivilizationName()))

	def onUnitKilled(self, argsList):
		'Unit Killed'
		pUnit, iKillerPlayer = argsList
		gc              = CyGlobalContext()
		cf              = self.cf
		getInfoType     = gc.getInfoTypeForString
		map             = CyMap()
		game            = CyGame()
		iLoserPlayer    = pUnit.getOwner()
		pKillerPlayer   = gc.getPlayer(iKillerPlayer)
		pLoserPlayer    = gc.getPlayer(iLoserPlayer)
		Civ             = self.Civilizations
		Rel             = self.Religions
		Promo           = self.Promotions["Effects"]
		Generic         = self.Promotions["Generic"]
		Race            = self.Promotions["Race"]
		Hero            = self.Heroes
		Trait           = self.Traits
		iLoserCiv       = pLoserPlayer.getCivilizationType()
		iRel            = pUnit.getReligion()
		iUnitType       = pUnit.getUnitType()
		iUnitCombat     = pUnit.getUnitCombatType()
		pPlot           = pUnit.plot()
		getPlot         = map.plot
		giftUnit        = cf.giftUnit
		getXP           = pUnit.getExperienceTimes100
		hasPromo        = pUnit.isHasPromotion
		Tech            = self.Techs
		getCivActive    = game.getNumCivActive
		Infernal        = self.Units["Infernal"]
		Mercurian       = self.Units["Mercurian"]
		Building        = self.Buildings
		UnitCombat      = self.UnitCombats
		addMsg          = CyInterface().addMessage
		getText         = CyTranslator().getText
		iNoAI           = UnitAITypes.NO_UNITAI
		iSouth          = DirectionTypes.DIRECTION_SOUTH
		randNum         = CyGame().getSorenRandNum

		if (pUnit.isAlive() and not pUnit.isImmortal() and (gc.isNoCrash() or not( pUnit.isOnDeathList()))):
			iX = pUnit.getX()
			iY = pUnit.getY()
			for iiX,iiY in RANGE1:
				pPlot2 = getPlot(iX+iiX,iY+iiY)
				if pPlot2.isCity():
					pCity = pPlot2.getPlotCity()
					if pCity.getNumBuilding( Building["Soul Forge"]) > 0:
						pCity.changeProduction(getXP()/100 + 10)
						addMsg(pCity.getOwner(),True,25,getText("TXT_KEY_MESSAGE_SOUL_FORGE",()),'AS2D_DISCOVERBONUS',1,'Art/Interface/Buttons/Buildings/Soulforge.dds',ColorTypes(7),pCity.getX(),pCity.getY(),True,True)
					if gc.getPlayer(pCity.getOwner()).hasTrait(Trait["Lycanthropic"]):
						pCity.changeFood(getXP()/100 + 10)
						addMsg(pCity.getOwner(),True,25,getText("TXT_KEY_MESSAGE_CANNIBALIZE",()),'AS2D_DISCOVERBONUS',1,'Art/Interface/Buttons/Promotions/Cannibalize.dds',ColorTypes(7),pCity.getX(),pCity.getY(),True,True)
		
			pPlot = getPlot(iX,iY)
			if pPlot.isCity():
				pCity = pPlot.getPlotCity()
				if pCity.getNumBuilding( Building["Mokkas Cauldron"]) > 0:
					if pCity.getOwner() == iLoserPlayer:
						iUnit = cf.getUnholyVersion(pUnit)
						if iUnit != -1:
							newUnit = pLoserPlayer.initUnit(iUnit, pCity.getX(), pCity.getY(), iNoAI, iSouth)
							newUnit.setHasPromotion( Race["Demon"], True)
							newUnit.setDamage(50, PlayerTypes.NO_PLAYER)
							newUnit.finishMoves()
							szBuffer = gc.getUnitInfo(newUnit.getUnitType()).getDescription()
							addMsg(iLoserPlayer,True,25,getText("TXT_KEY_MESSAGE_MOKKAS_CAULDRON",((szBuffer, ))),'AS2D_DISCOVERBONUS',1,'Art/Interface/Buttons/Buildings/MokkasCauldron.dds',ColorTypes(7),pCity.getX(),pCity.getY(),True,True)

			if game.countKnownTechNumTeams(Tech["Infernal Pact"]) > 0 and game.getNumCivActive(Civ["Infernal"]) > 0:
				if cf.angelorMane(pUnit)== gc.getInfoTypeForString('UNIT_MANES'):
					#add the bradeline well and the chance
					if not gc.isNoCrash():
						game.addtoDeathList(getInfoType('DEATHLIST_DEMON_CONVERSION'),pUnit)
					else:
						giftUnit( Infernal["Manes"], Civ["Infernal"], 0, pPlot, iLoserPlayer)
					addMsg(iLoserPlayer,True,25,getText("TXT_KEY_MESSAGE_UNIT_FALLS",()),'AS2D_UNIT_FALLS',1,'Art/Interface/Buttons/Promotions/Races/Demon.dds',ColorTypes(7),pPlot.getX(),pPlot.getY(),True,True)
			
			if game.getBuildingClassCreatedCount(Building["Mercurian Gate"]) > 0 and getCivActive(Civ["Mercurians"]) > 0:
				if cf.angelorMane(pUnit)== gc.getInfoTypeForString('UNIT_ANGEL'):
					#add the chance and whatever else is needed
					if not gc.isNoCrash():
						game.addtoDeathList(getInfoType('DEATHLIST_ANGEL_CONVERSION'),pUnit)
					else:
						giftUnit( Mercurian["Angel"], Civ["Mercurians"], getXP(), pPlot, iLoserPlayer)
					addMsg(iLoserPlayer,True,25,getText("TXT_KEY_MESSAGE_UNIT_RISES",()),'AS2D_UNIT_FALLS',1,'Art/Interface/Buttons/Promotions/Races/Angel.dds',ColorTypes(7),pPlot.getX(),pPlot.getY(),True,True)


			# Spirit Guide
			if hasPromo( Promo["Spirit Guide"]):
				if pUnit.getExperience() > 0:
					lUnits = []
					for pLoopUnit in PyPlayer(iLoserPlayer).getUnitList(): # getUnitList() cannot be used with pPlayer
						if pLoopUnit.isAlive():
							if not pLoopUnit.isOnlyDefensive():
								if not pLoopUnit.isDelayedDeath():
									lUnits.append(pLoopUnit)
					if len(lUnits) > 0:
						pUnit = lUnits[randNum(len(lUnits), "Spirit Guide")-1]
						iXP = getXP() / 2 # Experience of the dying unit
						pUnit.changeExperienceTimes100( iXP, -1, False, False, False)
						addMsg(iLoserPlayer,True,25,getText("TXT_KEY_MESSAGE_SPIRIT_GUIDE",()),'AS2D_DISCOVERBONUS',1,'Art/Interface/Buttons/Promotions/SpiritGuide.dds',ColorTypes(7),pUnit.getX(),pUnit.getY(),True,True)
			# Spirit Guide END
			
			if hasPromo(Promo["Aspect Capria"]):
				game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_CAPRIA'),False)
				pUnit.setHasPromotion(Promo["Aspect Capria"], False)
			if hasPromo(Promo["Aspect Mahon"]):
				game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_MAHON'),False)
				pUnit.setHasPromotion(Promo["Aspect Mahon"], False)
			if hasPromo(Promo["Aspect Magnadine"]):
				game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_MAGNADINE'),False)
				pUnit.setHasPromotion(Promo["Aspect Magnadine"], False)
			if hasPromo(Promo["Aspect Arak"]):
				game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_ARAK'),False)
				pUnit.setHasPromotion(Promo["Aspect Arak"], False)
			if hasPromo(Promo["Aspect Orthus"]):
				game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_ORTHUS'),False)
				pUnit.setHasPromotion(Promo["Aspect Orthus"], False)
			if hasPromo(Promo["Aspect Unknown1"]):
				game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_UNKNOWN_1'),False)
				pUnit.setHasPromotion(Promo["Aspect Unknown1"], False)
			if hasPromo(Promo["Aspect Unknown2"]):
				game.setGlobalFlag(gc.getInfoTypeForString('FLAG_ASPECT_OF_WAR_UNKNOWN_2'),False)
				pUnit.setHasPromotion(Promo["Aspect Unknown2"], False)
			
		if iUnitType == Hero["Acheron"]:
			pUnit.setHasPromotion(Promo["Acheron Leashed"], False)

		if game.getWBMapScript():
			sf.onUnitKilled(pUnit, iKillerPlayer)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitKilled']:
			module.onUnitKilled(self, argsList)

		## Modular Python End
		## *******************


		if (not self.__LOG_UNITKILLED):
			return
		CvUtil.pyPrint('Player %d Civilization %s Unit %s was killed by Player %d'
			%(pLoserPlayer.getID(), pLoserPlayer.getCivilizationDescription(0), PyInfo.UnitInfo(iUnitType).getDescription(), pKillerPlayer.getID()))

	def onUnitLost(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Unit Lost'
		pUnit = argsList[0]
		player = PyPlayer(pUnit.getOwner())

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitLost']:
			module.onUnitLost(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_UNITLOST):
			return
		CvUtil.pyPrint('%s was lost by Player %d Civilization %s'
			%(PyInfo.UnitInfo(pUnit.getUnitType()).getDescription(), player.getID(), player.getCivilizationName()))

	def onUnitPromoted(self, argsList):
		'Unit Promoted'
		self.verifyLoaded(True)

		pUnit, iPromotion = argsList
		player 		= PyPlayer(pUnit.getOwner())
		hasPromo 	= pUnit.isHasPromotion
		iUnitType 	= pUnit.getUnitType()
		Promo		= self.Promotions["Effects"]
		Race		= self.Promotions["Race"]
		Generic		= self.Promotions["Generic"]
		Sheaim		= self.Units["Sheaim"]
		Scions		= self.Units["Scions"]
		UnitAI		= self.UnitAI
# Trying to get high experienced units out of City Defense Notque 03/10/09
		if hasPromo(Promo["Hero"]):
			if pUnit.getExperience() > 25:
				if pUnit.getUnitAIType() != UnitAI["Counter"]:
					pUnit.setUnitAIType(UnitAI["Counter"])

		# Change to see if I can get Pyre Zombies to stop City Defense Notque 03/10/09
		if iUnitType == Sheaim["Pyre Zombie"]:
			if pUnit.getUnitAIType() == UnitAI["City Defense"]:
				if CyGame().getSorenRandNum(100, "PYRE_UNITAI") >= 50:
					pUnit.setUnitAIType(UnitAI["Collateral"])
				else:
					pUnit.setUnitAIType(UnitAI["Counter"])

#scions start - Handles Centeni promotions, makes sure they lose Undead status and get Chosen promotion when upgraded to another unit type
		if hasPromo(Promo["Unreliable"]):
			if iUnitType != Scions["Centeni"] or hasPromo(Generic["Headless"]):
				pUnit.setHasPromotion(Promo["Alive"], False)
				pUnit.setHasPromotion(Race["Undead"], True)
				pUnit.setHasPromotion(Promo["Chosen"], True)
				pUnit.setHasPromotion(Promo["Unreliable"], False)

# scions end


		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitPromoted']:
			module.onUnitPromoted(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_UNITPROMOTED):
			return
		CvUtil.pyPrint('Unit Promotion Event: %s - %s' %(player.getCivilizationName(), pUnit.getName(),))

	def onUnitSelected(self, argsList):
		'Unit Selected'
		unit = argsList[0]
		player = PyPlayer(unit.getOwner())

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitSelected']:
			module.onUnitSelected(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_UNITSELECTED):
			return
		CvUtil.pyPrint('%s was selected by Player %d Civilization %s'
			%(PyInfo.UnitInfo(unit.getUnitType()).getDescription(), player.getID(), player.getCivilizationName()))

	def onUnitRename(self, argsList):
		'Unit is renamed'
		pUnit = argsList[0]
		if (pUnit.getOwner() == CyGame().getActivePlayer()):
			self.__eventEditUnitNameBegin(pUnit)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitRename']:
			module.onUnitRename(self, argsList)

		## Modular Python End
		## *******************

	def onUnitPillage(self, argsList):
		'Unit pillages a plot'
		pUnit, iImprovement, iRoute, iOwner = argsList
		iPlotX                              = pUnit.getX()
		iPlotY                              = pUnit.getY()
		iUnitType                           = pUnit.getUnitType()
		gc                                  = CyGlobalContext()
		getInfoType                         = gc.getInfoTypeForString
		map                                 = CyMap()
		pPlot                               = map.plot(iPlotX, iPlotY)
		pPlayer                             = gc.getPlayer(iOwner)
		if (pPlot.isOwned()):
			pVictim                             = gc.getPlayer(pPlot.getOwner())
		Status                              = self.LeaderStatus
		Trait                               = self.Traits
		iJotnar                             = gc.getInfoTypeForString('CIVILIZATION_JOTNAR')

		#if pPlayer.getLeaderStatus() == Status["Important"] and not pPlayer.hasTrait(Trait["Raiders"]):
		#	if CyGame().getSorenRandNum(100, "Bob") <= 3:
		#		pPlayer.initTriggeredData(self.EventTriggers["Raiders"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		#Mekara Units - Slave Raids
		if iUnitType == gc.getInfoTypeForString('UNIT_BOUNTY_HUNTER') or iUnitType == gc.getInfoTypeForString('UNIT_SLAVE_HUNTER') or iUnitType == gc.getInfoTypeForString('UNIT_RAIDER'):
			sValidImprovements = ['IMPROVEMENT_PASTURE','IMPROVEMENT_FARM','IMPROVEMENT_HOMESTEAD','IMPROVEMENT_COTTAGE','IMPROVEMENT_HAMLET','IMPROVEMENT_VILLAGE','IMPROVEMENT_TOWN','IMPROVEMENT_ENCLAVE','IMPROVEMENT_PLANTATION' ,'IMPROVEMENT_DWARVEN_SETTLEMENT','IMPROVEMENT_DWARVEN_HALL','IMPROVEMENT_DWARVEN_FORTRESS','IMPROVEMENT_DWARVEN_MINE','IMPROVEMENT_BEDOUIN_CAMP','IMPROVEMENT_BEDOUIN_GATHERING','IMPROVEMENT_BEDOUIN_VILLAGE','IMPROVEMENT_BEDOUIN_SIT']
			iRnd = CyGame().getSorenRandNum(100, "Capture Chance")
			if (iUnitType == gc.getInfoTypeForString('UNIT_BOUNTY_HUNTER') and iRnd < 20) or (iUnitType == gc.getInfoTypeForString('UNIT_SLAVE_HUNTER') and iRnd < 30) or (iUnitType == gc.getInfoTypeForString('UNIT_RAIDER') and iRnd < 40):
				for i in xrange (0, len(sValidImprovements)) :
					iImprovement2 =  gc.getInfoTypeForString (sValidImprovements[i])
					if iImprovement == iImprovement2 :
						CvUtil.pyPrint("While pillaging, Player %d's %s captured a slave" %(iOwner, PyInfo.UnitInfo(iUnitType).getDescription()))
						iUnit = gc.getInfoTypeForString("UNIT_SLAVE")
						if pPlot.isOwned():
							if iJotnar != -1:
								if gc.getCivilizationInfo(pVictim.getCivilizationType()) == iJotnar:
									iUnit = gc.getInfoTypeForString("UNIT_JOT_SLAVE")
						newUnit = pPlayer.initUnit(iUnit,iPlotX, iPlotY, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
						if pPlot.isOwned():
							pVictimCiv = gc.getCivilizationInfo(pVictim.getCivilizationType()) # test Ronkhar
							iRace = pVictimCiv.getDefaultRace()
							if iRace != -1:
								newUnit.setHasPromotion(iRace, True)
		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitPillage']:
			module.onUnitPillage(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_UNITPILLAGE):
			return
		CvUtil.pyPrint("Player %d's %s pillaged improvement %d and route %d at plot at (%d, %d)"
			%(iOwner, PyInfo.UnitInfo(iUnitType).getDescription(), iImprovement, iRoute, iPlotX, iPlotY))

	def onUnitSpreadReligionAttempt(self, argsList):
		'Unit tries to spread religion to a city'
		pUnit, iReligion, bSuccess = argsList
		map = CyMap()

		iX = pUnit.getX()
		iY = pUnit.getY()
		pPlot = map.plot(iX, iY)
		pCity = pPlot.getPlotCity()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitSpreadReligionAttempt']:
			module.onUnitSpreadReligionAttempt(self, argsList)

		## Modular Python End
		## *******************

	def onUnitGifted(self, argsList):
		'Unit is gifted from one player to another'
		pUnit, iGiftingPlayer, pPlotLocation = argsList

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitGifted']:
			module.onUnitGifted(self, argsList)

		## Modular Python End
		## *******************

	def onUnitBuildImprovement(self, argsList):
		'Unit begins enacting a Build (building an Improvement or Route)'
		pUnit, iBuild, bFinished = argsList

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onUnitBuildImprovement']:
			module.onUnitBuildImprovement(self, argsList)

		## Modular Python End
		## *******************

	def onGoodyReceived(self, argsList):
		'Goody received'
		iPlayer, pPlot, pUnit, iGoodyType = argsList
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onGoodyReceived']:
			module.onGoodyReceived(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_GOODYRECEIVED):
			return
		CvUtil.pyPrint('%s received a goody' %(gc.getPlayer(iPlayer).getCivilizationDescription(0)),)

	def onGreatPersonBorn(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Unit Promoted'
		pUnit, iPlayer, pCity = argsList
		gc 			= CyGlobalContext() #Cause local variables are faster
		getInfoType	= gc.getInfoTypeForString
		game = CyGame()
		player = PyPlayer(iPlayer)
		pPlayer = gc.getPlayer(iPlayer)
		Status 	= self.LeaderStatus
		Trait 	= self.Traits

		#if pPlayer.getLeaderStatus() == Status["Important"] and not pPlayer.hasTrait(Trait["Philosophical"]):
		#	if game.getSorenRandNum(100, "Bob") <= 10:
		#		pPlayer.initTriggeredData(self.EventTriggers["Philosophical"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onGreatPersonBorn']:
			module.onGreatPersonBorn(self, argsList)

		## Modular Python End
		## *******************

		if pUnit.isNone() or pCity.isNone():
			return
		if (not self.__LOG_GREATPERSON):
			return
		CvUtil.pyPrint('A %s was born for %s in %s' %(pUnit.getName(), player.getCivilizationName(), pCity.getName()))

	def onTechAcquired(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Tech Acquired'
		iTechType, iTeam, iPlayer, bAnnounce = argsList
		# Note that iPlayer may be NULL (-1) and not a refer to a player object
		self.verifyLoaded()

		gc = CyGlobalContext()
		getInfoType	= gc.getInfoTypeForString
		cf			= self.cf
		game 		= CyGame()
		map 		= CyMap()
		plotByIndex = map.plotByIndex
		randNum 	= game.getSorenRandNum
		getPlayer 	= gc.getPlayer
		getTeam 	= gc.getTeam
		Option		= self.GameOptions
		Tech		= self.Techs
		Civ			= self.Civilizations
		Leader		= self.Leaders
		Rel			= self.Religions
		Trait		= self.Traits
		Status		= self.LeaderStatus
		Promo		= self.Promotions["Effects"]
		Race		= self.Promotions["Race"]
		Generic		= self.Promotions["Generic"]
		Unit		= self.Units
		iNoAI		= UnitAITypes.NO_UNITAI
		iNorth		= DirectionTypes.DIRECTION_NORTH
		iLeader 	= getPlayer(iPlayer).getLeaderType()
		
		# Show tech splash when applicable
		if (iPlayer > -1 and bAnnounce and not CyInterface().noTechSplash()):
			if (game.isFinalInitialized() and not game.GetWorldBuilderMode()):
				if ((not game.isNetworkMultiPlayer()) and (iPlayer == game.getActivePlayer())):
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
					popupInfo.setData1(iTechType)
					popupInfo.setText(u"showTechSplash")
					popupInfo.addPopup(iPlayer)

		if (iPlayer != -1 and iPlayer != gc.getORC_PLAYER() and iPlayer != gc.getANIMAL_PLAYER() and iPlayer != gc.getDEMON_PLAYER()):
			pPlayer = getPlayer(iPlayer)
			iReligion = -1
			if   iTechType == Tech["Corruption of Spirit"]:
				iUnit 		= self.Units["Veil"]["Disciple"]
				iReligion   = Rel["Ashen Veil"]
			elif iTechType == Tech["Orders from Heaven"]:
				iUnit  		= self.Units["Order"]["Disciple"]
				iReligion   = Rel["Order"]
			elif iTechType == Tech["Way of the Forests"]:
				iUnit 		= self.Units["Leaves"]["Disciple"]
				iReligion   = Rel["Fellowship"]
			elif iTechType == Tech["Way of the Earthmother"]:
				iUnit 		= self.Units["Runes"]["Disciple"]
				iReligion   = Rel["Runes of Kilmorph"]
			elif iTechType == Tech["Message from the Deep"]:
				iUnit 		= self.Units["Overlords"]["Disciple"]
				iReligion   = Rel["Octopus Overlords"]
			elif iTechType == Tech["Honor"]:
				iUnit 		= self.Units["Empyrean"]["Disciple"]
				iReligion   = Rel["Empyrean"]
			elif iTechType == Tech["Deception"]:
				iUnit 		= self.Units["Esus"]["Nightwatch"]
				iReligion   = Rel["Council of Esus"]
			elif iTechType == Tech["White Hand"]:
				iUnit 		= self.Units["White Hand"]["Disciple"]
				iReligion   = Rel["White Hand"]
			if iReligion   != -1:
				if game.isReligionFounded(iReligion):
					if cf.canReceiveReligionUnit(pPlayer):# Ronkhar TODO: check if this line has any use (notably check with dural, mazatl UU, and religion tech trading)
						cf.giftUnit(iUnit, pPlayer.getCivilizationType(), 0, -1, -1)

		# TECH_INFERNAL_PACT Start
		if not gc.getGame().isOption(GameOptionTypes.GAMEOPTION_NO_HYBOREM_OR_BASIUM):
			lDemonLordsList= [getInfoType("LEADER_HYBOREM")]
			lDemonLordsTraitList=["TRAIT_PACT_HYBOREM"]
			lDemonLordsHelpTraitList=["EVENT_PYHELP_TRAIT_HYBOREM"]
			lDemonLordsHelpPactList=["EVENT_PYHELP_PACT_HYBOREM"]
			
			if (getInfoType("MODULE_IMPORTANT_LEADERS")!=-1):
				lDemonLordsList=lDemonLordsList+[getInfoType("LEADER_MERESIN"),getInfoType("LEADER_OUZZA"),getInfoType("LEADER_STATIUS"),getInfoType("LEADER_SALLOS"),getInfoType("LEADER_LETHE"),getInfoType("LEADER_JUDECCA")]
				lDemonLordsTraitList=lDemonLordsTraitList+["TRAIT_PACT_MERESIN","TRAIT_PACT_OUZZA","TRAIT_PACT_STATIUS","TRAIT_PACT_SALLOS","TRAIT_PACT_LETHE","TRAIT_PACT_JUDECCA"]
				lDemonLordsHelpTraitList=lDemonLordsHelpTraitList+["EVENT_PYHELP_TRAIT_MERESIN","EVENT_PYHELP_TRAIT_OUZZA","EVENT_PYHELP_TRAIT_STATIUS","EVENT_PYHELP_TRAIT_SALLOS","EVENT_PYHELP_TRAIT_LETHE","EVENT_PYHELP_TRAIT_JUDECCA"]
				lDemonLordsHelpPactList=lDemonLordsHelpPactList+["EVENT_PYHELP_PACT_MERESIN","EVENT_PYHELP_PACT_OUZZA","EVENT_PYHELP_PACT_STATIUS","EVENT_PYHELP_PACT_SALLOS","EVENT_PYHELP_PACT_LETHE","EVENT_PYHELP_PACT_JUDECCA"]
			if (iTechType == getInfoType("TECH_INFERNAL_PACT") and iPlayer != -1 and iPlayer != gc.getORC_PLAYER() and iPlayer != gc.getANIMAL_PLAYER() and iPlayer != gc.getDEMON_PLAYER() and not iLeader in lDemonLordsList ):
				lDemonLordsToSpawn = []
				lDemonLordsTraitToSpawn = []
				lDemonLordsHelpTraitClean = []
				lDemonLordsHelpPactClean = []
				for iDemonLord in range(len(lDemonLordsList)):
					if not CyGame().isLeaderEverActive(lDemonLordsList[iDemonLord]):
						lDemonLordsToSpawn.append(lDemonLordsList[iDemonLord])
						lDemonLordsTraitToSpawn.append(lDemonLordsTraitList[iDemonLord])
						lDemonLordsHelpTraitClean.append(lDemonLordsHelpTraitList[iDemonLord])
						lDemonLordsHelpPactClean.append(lDemonLordsHelpPactList[iDemonLord])
				if lDemonLordsToSpawn:
					if gc.getPlayer(iPlayer).isHuman() and not CyGame().GetWorldBuilderMode():
						popupInfo = CyPopupInfo()
						popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
						popupInfo.setText(CyTranslator().getText("TXT_KEY_PICK_DEMON_LORD",()))
						popupInfo.setData1(iPlayer)
						popupInfo.setData3(103) # onModNetMessage id
						popupInfo.setOnClickedPythonCallback("passToModNetMessage")
						popupInfo.setOption2(True); #Activate WIDGET HELP in buttons
						popupInfo.setFlags(126);  #165 is WIDGET_HELP_EVENT
						for i in range(len(lDemonLordsToSpawn)):
							popupInfo.addPythonButton(localText.getText("TXT_KEY_SPAWN_DEMON_LORD", (gc.getLeaderHeadInfo(lDemonLordsToSpawn[i]).getDescription(),)),lDemonLordsHelpTraitClean[i] )
							popupInfo.addPythonButton(localText.getText("TXT_KEY_START_AS_DEMON_LORD", (gc.getLeaderHeadInfo(lDemonLordsToSpawn[i]).getDescription(),)), lDemonLordsHelpPactClean[i])
						popupInfo.addPopup(iPlayer)
					else:
						irandid =CyGame().getSorenRandNum(len(lDemonLordsToSpawn), "Random Infernal Lord")
						iLeader = lDemonLordsToSpawn[irandid]
						iTrait  = getInfoType(lDemonLordsTraitToSpawn[irandid])
						cf.spawnDemonLord(iLeader,iPlayer)
						getPlayer(iPlayer).setHasTrait(iTrait,True)
				# If LEADER_HYBOREM is spawned outside of Infernal Pact without UNIT_HYBOREM, it will get UNIT_HYBOREM on next Infernal Pact researched and every other Demon Lord spawned.
				elif CyGame().isLeaderEverActive(getInfoType("LEADER_HYBOREM")) and not CyGame().isUnitClassMaxedOut(getInfoType("UNITCLASS_HYBOREM"), 0):
					pInfernalPlayer	= getPlayer(game.getCivActivePlayer(getInfoType("CIVILIZATION_INFERNAL"), 0))
					pCapital		= pInfernalPlayer.getCapitalCity()
					if not pCapital.isNone():
						NewUnit		= pInfernalPlayer.initUnit(git("UNIT_HYBOREM"),pCapital.getX(),pCapital.getY(),UnitAITypes.NO_UNITAI,DirectionTypes.DIRECTION_SOUTH)
						NewUnit.setHasPromotion(git("PROMOTION_IMMORTAL"), True)
						NewUnit.setHasCasted(True)
						NewUnit.setExperienceTimes100(2500, -1)
		# TECH_INFERNAL_PACT End

		# if (iPlayer != -1):
			# pPlayer 		 = getPlayer(iPlayer)
			# iLeaderStatus 	 = pPlayer.getLeaderStatus()
			# if iLeaderStatus == Status["Important"]:
				# trigger	 	 	 = pPlayer.initTriggeredData
				# findInfo 		 = CvUtil.findInfoTypeNum
				# getNumTriggers 	 = gc.getNumEventTriggerInfos
				# eventTriggerInfo = gc.getEventTriggerInfo
				# hasTrait 		 = pPlayer.hasTrait
				# Event			 = self.EventTriggers

				# iRand  = randNum(100, "Bob")
				# iRand2 = randNum(100, "Bob")

				# if   iTechType == Tech["Construction"]:
					# if not hasTrait( Trait["Industrious"]) and iRand <= 3:
						# trigger( Event["Industrious"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Expansive"]) and iRand2 <= 5:
							# trigger( Event["Expansive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Smelting"]:
					# if not hasTrait( Trait["Industrious"]) and iRand <= 10:
						# trigger( Event["Industrious"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Aggressive"]) and iRand2 <= 5:
							# trigger( Event["Aggressive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Engineering"]:
					# if not hasTrait( Trait["Industrious"]) and iRand <= 20:
						# trigger(Event["Industrious"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Expansive"]) and iRand2 <= 5:
							# trigger(Event["Expansive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Trade"]:
					# if not hasTrait( Trait["Financial"]) and iRand <= 10:
						# trigger(Event["Financial"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)
						# if not hasTrait( Trait["Ingenuity"]) and iRand2 <= 5:
							# trigger(Event["Ingenuity"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Currency"]:
					# if not hasTrait( Trait["Financial"]) and iRand <= 20:
						# trigger(Event["Financial"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Organized"]) and iRand2 <= 5:
							# trigger(Event["Organized"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Math"]:
					# if not hasTrait( Trait["Financial"]) and iRand <= 50:
						# trigger(Event["Financial"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Philosophical"]) and iRand2 <= 5:
							# trigger(Event["Philosophical"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Code of Laws"]:
					# if not hasTrait( Trait["Organized"]) and iRand <= 3:
						# trigger(Event["Organized"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Financial"]) and iRand2 <= 5:
							# trigger(Event["Financial"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Military Strategy"]:
					# if not hasTrait( Trait["Organized"]) and iRand <= 20:
						# trigger(Event["Organized"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Aggressive"]) and iRand2 <= 5:
							# trigger(Event["Aggressive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Writing"]:
					# if not hasTrait( Trait["Philosophical"]) and iRand <= 3:
						# trigger(Event["Philosophical"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Creative"]) and iRand2 <= 5:
							# trigger(Event["Creative"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

					# if not hasTrait( Trait["Expansive"]) and randNum(100, "Bob") <= 10:
						# trigger(Event["Expansive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Ingenuity"]) and randNum(100, "Bob") <= 5:
							# trigger(Event["Ingenuity"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

					# if not hasTrait( Trait["Creative"]) and randNum(100, "Bob") <= 3:
						# trigger(Event["Creative"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Ingenuity"]) and randNum(100, "Bob") <= 5:
							# trigger(Event["Ingenuity"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)


				# elif iTechType == Tech["Philosophy"]:
					# if not hasTrait( Trait["Philosophical"]) and iRand <= 50:
						# trigger(Event["Philosophical"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Creative"]) and iRand2 <= 5:
							# trigger(Event["Creative"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Medicine"]:
					# if not hasTrait( Trait["Expansive"]) and iRand <= 20:
						# trigger(Event["Expansive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Ingenuity"]) and iRand2 <= 5:
							# trigger(Event["Ingenuity"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Drama"]:
					# if not hasTrait( Trait["Creative"]) and iRand <= 20:
						# trigger(Event["Creative"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Ingenuity"]) and iRand2 <= 5:
							# trigger(Event["Ingenuity"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Feudalism"]:
					# if not hasTrait( Trait["Ingenuity"]) and iRand <= 20:
						# trigger(Event["Ingenuity"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Creative"]) and iRand2 <= 5:
							# trigger(Event["Creative"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Knowledge of the Ether"]:
					# if not hasTrait( Trait["Arcane"]) and iRand <= 5:
						# trigger(Event["Arcane"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Summoner"]) and iRand2 <= 5:
							# trigger(Event["Summoner"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

					# if not hasTrait( Trait["Summoner"]) and randNum(100, "Bob") <= 3:
						# trigger(Event["Summoner"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Arcane"]) and randNum(100, "Bob") <= 5:
							# trigger(Event["Arcane"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Sorcery"]:
					# if not hasTrait( Trait["Arcane"]) and iRand <= 50:
						# trigger(Event["Arcane"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Summoner"]) and iRand2 <= 5:
							# trigger(Event["Summoner"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

					# if not hasTrait( Trait["Summoner"]) and randNum(100, "Bob") <= 50:
						# trigger(Event["Summoner"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

						# if not hasTrait( Trait["Arcane"]) and randNum(100, "Bob") <= 5:
							# trigger(Event["Arcane"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

				# elif iTechType == Tech["Optics"]:
					# if not hasTrait( Trait["Swashbuckler"]):
						# trigger(Event["Swashbuckler"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)
		if game.getWBMapScript():
			sf.onTechAcquired(iTechType, iTeam, iPlayer, bAnnounce)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onTechAcquired']:
			module.onTechAcquired(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_TECH):
			return
		CvUtil.pyPrint('%s was finished by Team %d'
			%(PyInfo.TechnologyInfo(iTechType).getDescription(), iTeam))

	def onTechSelected(self, argsList):
		'Tech Selected'
		iTechType, iPlayer = argsList

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onTechSelected']:
			module.onTechSelected(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_TECH):
			return
		CvUtil.pyPrint('%s was selected by Player %d' %(PyInfo.TechnologyInfo(iTechType).getDescription(), iPlayer))


	def onTraitGained(self, argsList):
		'Trait Gained'
		iTrait, iPlayer = argsList
		gc = CyGlobalContext()
		game 		= CyGame()
		getPlayer 		= gc.getPlayer
		pPlayer=getPlayer(iPlayer)
		Status			= self.LeaderStatus
		bAI		 		= not pPlayer.isHuman()
		if (iTrait == gc.getInfoTypeForString('TRAIT_CIVILIZED')): # Barbarians declare war on the Clan if it becomes too strong; re-added by Azatote
			eTeam = gc.getTeam(gc.getPlayer(gc.getORC_PLAYER()).getTeam())
			iTeam = pPlayer.getTeam()
			if eTeam.isAtWar(iTeam) == False:
				eTeam.declareWar(iTeam, False, WarPlanTypes.WARPLAN_LIMITED)
				if (iPlayer == game.getActivePlayer() and not bAI):
					addPopup(CyTranslator().getText("TXT_KEY_POPUP_BARBARIAN_DECLARE_WAR",()), 'art/interface/popups/Barbarian.dds')
	
		if (iTrait == gc.getInfoTypeForString("TRAIT_KAHD_OGHMA")):
			pPlayer.setHasTrait(gc.getInfoTypeForString("TRAIT_INTOLERANT"),False)
			pPlayer.setHasTrait(gc.getInfoTypeForString("TRAIT_SPIRITUAL"),True)
			addPopup(CyTranslator().getText("TXT_KEY_POPUP_KAHDI_STRENGTH_OF_WILL",()), 'art/interface/popups/kahdpop.dds')
			addPopup(CyTranslator().getText("TXT_KEY_POPUP_KAHDI_ENLIGHTENMENT",()), 'art/interface/popups/enlightenment.dds')
		
		if (iTrait == gc.getInfoTypeForString("TRAIT_KAHD_MAMMON")):
			addPopup(CyTranslator().getText("TXT_KEY_POPUP_KAHDI_STRENGTH_OF_WILL",()), 'art/interface/popups/kahdpop.dds')
			addPopup(CyTranslator().getText("TXT_KEY_POPUP_KAHDI_CORRUPTION",()), 'art/interface/popups/corruption.dds')
		
	#	if (pPlayer.isHuman() and pPlayer.getLeaderStatus()==gc.getInfoTypeForString("IMPORTANT_STATUS") and gc.getTraitInfo(iTrait).getTraitClass() == gc.getInfoTypeForString("TRAITCLASS_PERSONALITY")):
	#		popupInfo = CyPopupInfo()
	#		popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
	#		popupInfo.setText(CyTranslator().getText("TXT_KEY_TRAIT_GAIN_CHOICE",(gc.getTraitInfo(iTrait).getDescription(),)))
	#		popupInfo.setData1(iTrait)
	#		popupInfo.setData2(iPlayer)
	#		popupInfo.setPythonModule("CvRandomEventInterface")
	#		popupInfo.addPythonButton(localText.getText("TXT_KEY_POPUP_YES", ()), "")
	#		popupInfo.addPythonButton(localText.getText("TXT_KEY_POPUP_NO", ()), "")
	#		popupInfo.setOnClickedPythonCallback("removeTraitcallback")
	#		popupInfo.addPopup(iPlayer)
	
		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onTraitGained']:
			module.onTraitGained(self, argsList)

		## Modular Python End
		## *******************

	def onTraitLost(self, argsList):
		'Trait Lost'
		iTrait, iPlayer = argsList

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onTraitLost']:
			module.onTraitLost(self, argsList)

		## Modular Python End
		## *******************




	def onReligionFounded(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Religion Founded'
		iReligion, iFounder = argsList
		gc 			= CyGlobalContext() #Cause local variables are faster
		getInfoType	= gc.getInfoTypeForString
		game 		= CyGame()
		player 		= PyPlayer(iFounder)
		pPlayer 	= gc.getPlayer(iFounder)
		Status		= self.LeaderStatus
		Trait		= self.Traits
		Rel			= self.Religions

		#if (pPlayer.getLeaderStatus() == Status["Important"]) and not pPlayer.hasTrait(Trait["Spiritual"]):
		#	if game.getSorenRandNum(100, "Bob") <= 50:
		#		pPlayer.initTriggeredData(self.EventTriggers["Spiritual"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		iCityId = game.getHolyCity(iReligion).getID()
		if (game.isFinalInitialized() and not game.GetWorldBuilderMode()):
			if ((not game.isNetworkMultiPlayer()) and (iFounder == game.getActivePlayer())):
				popupInfo = CyPopupInfo()
				popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
				popupInfo.setData1(iReligion)
				popupInfo.setData2(iCityId)
				if (iReligion == Rel["Empyrean"] or iReligion == Rel["Council of Esus"]):
					popupInfo.setData3(3)
				else:
					popupInfo.setData3(1)
				popupInfo.setText(u"showWonderMovie")
				popupInfo.addPopup(iFounder)

		if game.getWBMapScript():
			sf.onReligionFounded(iReligion, iFounder)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onReligionFounded']:
			module.onReligionFounded(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_RELIGION):
			return
		CvUtil.pyPrint('Player %d Civilization %s has founded %s'
			%(iFounder, player.getCivilizationName(), gc.getReligionInfo(iReligion).getDescription()))

	def onReligionSpread(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Religion Has Spread to a City'
		iReligion, iOwner, pSpreadCity = argsList
		gc 			= CyGlobalContext() #Cause local variables are faster
		getInfoType	= gc.getInfoTypeForString
		game 		= CyGame()
		player 		= PyPlayer(iOwner)
		Rel			= self.Religions
		pPlayer 	= gc.getPlayer(iOwner)

		if iReligion == Rel["Order"] and game.getGameTurn() != game.getStartTurn():
			if (pPlayer.getStateReligion() == Rel["Order"] and pSpreadCity.getOccupationTimer() <= 0):
				if (game.getSorenRandNum(100, "Order Spawn") < self.Defines["Order Spawn"]):
					Order 	= self.Units["Order"]
					pTeam 	= gc.getTeam(pPlayer.getTeam())
					iSouth	= DirectionTypes.DIRECTION_SOUTH
					iNoAI	= UnitAITypes.NO_UNITAI
					if pTeam.isHasTech( self.Techs["Fanaticism"]):
						iUnit = Order["Crusader"]
						CyInterface().addMessage(iOwner,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_ORDER_SPAWN_CRUSADER",()),'AS2D_UNIT_BUILD_UNIT',1,'Art/Interface/Buttons/Units/Crusader.dds',ColorTypes(8),pSpreadCity.getX(),pSpreadCity.getY(),True,True)
					else:
						iUnit = Order["Disciple"]
						CyInterface().addMessage(iOwner,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_ORDER_SPAWN_ACOLYTE",()),'AS2D_UNIT_BUILD_UNIT',1,'Art/Interface/Buttons/Units/Disciple Order.dds',ColorTypes(8),pSpreadCity.getX(),pSpreadCity.getY(),True,True)
					newUnit = pPlayer.initUnit(iUnit, pSpreadCity.getX(), pSpreadCity.getY(), iNoAI, iSouth)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onReligionSpread']:
			module.onReligionSpread(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has spread to Player %d Civilization %s city of %s'
			%(gc.getReligionInfo(iReligion).getDescription(), iOwner, player.getCivilizationName(), pSpreadCity.getName()))

	def onReligionRemove(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Religion Has been removed from a City'
		iReligion, iOwner, pRemoveCity = argsList
		player = PyPlayer(iOwner)
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onReligionRemove']:
			module.onReligionRemove(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has been removed from Player %d Civilization %s city of %s'
			%(gc.getReligionInfo(iReligion).getDescription(), iOwner, player.getCivilizationName(), pRemoveCity.getName()))

	def onCorporationFounded(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Corporation Founded'
		iCorporation, iFounder = argsList
		player = PyPlayer(iFounder)
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCorporationFounded']:
			module.onCorporationFounded(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_RELIGION):
			return
		CvUtil.pyPrint('Player %d Civilization %s has founded %s'
			%(iFounder, player.getCivilizationName(), gc.getCorporationInfo(iCorporation).getDescription()))

	def onCorporationSpread(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Corporation Has Spread to a City'
		iCorporation, iOwner, pSpreadCity = argsList
		player = PyPlayer(iOwner)
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCorporationSpread']:
			module.onCorporationSpread(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has spread to Player %d Civilization %s city of %s'
			%(gc.getCorporationInfo(iCorporation).getDescription(), iOwner, player.getCivilizationName(), pSpreadCity.getName()))

	def onCorporationRemove(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Corporation Has been removed from a City'
		iCorporation, iOwner, pRemoveCity = argsList
		player = PyPlayer(iOwner)
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCorporationRemove']:
			module.onCorporationRemove(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has been removed from Player %d Civilization %s city of %s'
			%(gc.getCorporationInfo(iCorporation).getDescription(), iOwner, player.getCivilizationName(), pRemoveCity.getName()))

	def onGoldenAge(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Golden Age'
		iPlayer = argsList[0]
		gc = CyGlobalContext() #Cause local variables are faster
		getInfoType	= gc.getInfoTypeForString
		player 		= PyPlayer(iPlayer)
		pPlayer 	= gc.getPlayer(iPlayer)
		Status		= self.LeaderStatus
		Trait		= self.Traits

		#if (pPlayer.getLeaderStatus() == Status["Important"]) and not pPlayer.hasTrait( Trait["Magic Resistant"]):
		#	if not pPlayer.hasTrait( Trait["Ingenuity"]) and CyGame().getSorenRandNum(100, "Bob") <= 50:
		#		pPlayer.initTriggeredData(self.EventTriggers["Ingenuity"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onGoldenAge']:
			module.onGoldenAge(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_GOLDENAGE):
			return
		CvUtil.pyPrint('Player %d Civilization %s has begun a golden age'
			%(iPlayer, player.getCivilizationName()))

	def onEndGoldenAge(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'End Golden Age'
		iPlayer = argsList[0]
		player = PyPlayer(iPlayer)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onEndGoldenAge']:
			module.onEndGoldenAge(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_ENDGOLDENAGE):
			return
		CvUtil.pyPrint('Player %d Civilization %s golden age has ended'
			%(iPlayer, player.getCivilizationName()))

	def onChangeWar(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'War Status Changes'
		getInfoType		= gc.getInfoTypeForString
		
		bIsWar = argsList[0]
		iTeam = argsList[1]
		iRivalTeam = argsList[2]
		lDemonLordsList= [getInfoType("LEADER_HYBOREM")]
		lDemonLordsTraitList=["TRAIT_PACT_HYBOREM"]
		iMaxPlayers		= gc.getMAX_PLAYERS()
		
		if (getInfoType("MODULE_IMPORTANT_LEADERS")!=-1):
			lDemonLordsList=lDemonLordsList+[getInfoType("LEADER_MERESIN"),getInfoType("LEADER_OUZZA"),getInfoType("LEADER_STATIUS"),getInfoType("LEADER_SALLOS"),getInfoType("LEADER_LETHE"),getInfoType("LEADER_JUDECCA")]
			lDemonLordsTraitList=lDemonLordsTraitList+["TRAIT_PACT_MERESIN","TRAIT_PACT_OUZZA","TRAIT_PACT_STATIUS","TRAIT_PACT_SALLOS","TRAIT_PACT_LETHE","TRAIT_PACT_JUDECCA"]
			
		if (bIsWar):
			for iLoopPlayer in xrange(iMaxPlayers):
				if (gc.getPlayer(iLoopPlayer).getTeam()==iTeam) and gc.getPlayer(iLoopPlayer).getLeaderType() in lDemonLordsList :
					iDemonId = lDemonLordsList.index(gc.getPlayer(iLoopPlayer).getLeaderType())
					for iLoopPlayer2 in xrange(iMaxPlayers):
						if(gc.getPlayer(iLoopPlayer2).getTeam()==iRivalTeam):
							gc.getPlayer(iLoopPlayer2).setHasTrait(getInfoType(lDemonLordsTraitList[iDemonId]),False)
				
				if (gc.getPlayer(iLoopPlayer).getTeam()==iRivalTeam) and gc.getPlayer(iLoopPlayer).getLeaderType() in lDemonLordsList :
					iDemonId = lDemonLordsList.index(gc.getPlayer(iLoopPlayer).getLeaderType())
					for iLoopPlayer2 in xrange(iMaxPlayers):
						if(gc.getPlayer(iLoopPlayer2).getTeam()==iTeam):
							gc.getPlayer(iLoopPlayer2).setHasTrait(getInfoType(lDemonLordsTraitList[iDemonId]),False)
				
		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onChangeWar']:
			module.onChangeWar(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_WARPEACE):
			return
		if (bIsWar):
			strStatus = "declared war"
		else:
			strStatus = "declared peace"
		CvUtil.pyPrint('Team %d has %s on Team %d'
			%(iTeam, strStatus, iRivalTeam))

	def onChat(self, argsList):
		'Chat Message Event'
		chatMessage = "%s" %(argsList[0],)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onChat']:
			module.onChat(self, argsList)

		## Modular Python End
		## *******************

	def onSetPlayerAlive(self, argsList):
		'Set Player Alive Event'
		iPlayerID = argsList[0]
		bNewValue = argsList[1]
		gc 			= CyGlobalContext() #Cause local variables are faster
		cf			= self.cf
		getInfoType	= gc.getInfoTypeForString
		getPlayer 	= gc.getPlayer
		game 		= CyGame()
		CvUtil.pyPrint("Player %d's alive status set to: %d" %(iPlayerID, int(bNewValue)))

		if (bNewValue == False and game.getGameTurnYear() >= 5):
			pPlayer = getPlayer(iPlayerID)
			if pPlayer.getAlignment() == self.Alignments["Good"]:
				game.changeGlobalCounter(5)
			if pPlayer.getAlignment() == self.Alignments["Evil"]:
				game.changeGlobalCounter(-5)
			if game.getWBMapScript():
				sf.playerDefeated(pPlayer)
			else:
				if game.getAIAutoPlay() == 0:
					sPlayerName = pPlayer.getName()
					sQuote = gc.getLeaderHeadInfo(pPlayer.getLeaderType()).getDefeatQuote()
					sPopupText = CyTranslator().getText('TXT_KEY_MISC_DEFEAT_POPUP',(sPlayerName, sQuote))
					addPopup(sPopupText, str(gc.getLeaderHeadInfo(pPlayer.getLeaderType()).getImage()))

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onSetPlayerAlive']:
			module.onSetPlayerAlive(self, argsList)

		## Modular Python End
		## *******************

	def onPlayerChangeStateReligion(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'Player changes his state religion'
		iPlayer, iNewReligion, iOldReligion = argsList
		gc = CyGlobalContext() #Cause local variables are faster
		getInfoType	= gc.getInfoTypeForString
		getPlayer 	= gc.getPlayer
		pPlayer 	= getPlayer(iPlayer)
		getTeam		= gc.getTeam
		Rel			= self.Religions
		Civ			= self.Civilizations
		iCiv 		= pPlayer.getCivilizationType()

		if iOldReligion == Rel["Ashen Veil"] and iNewReligion != Rel["Ashen Veil"]:
			eDemonTeam = getTeam(getPlayer(gc.getDEMON_PLAYER()).getTeam())
			iTeam = pPlayer.getTeam()
			if eDemonTeam.isAtWar(iTeam) == False:
				eDemonTeam.declareWar(iTeam, False, WarPlanTypes.WARPLAN_TOTAL)

		if iNewReligion == Rel["Ashen Veil"] and (iCiv == Civ["Sheaim"] or iCiv == Civ["Infernal"]):
			iDemonTeam = gc.getDEMON_TEAM()
			pTeam = getTeam(pPlayer.getTeam())
			pTeam.makePeace(iDemonTeam)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onPlayerChangeStateReligion']:
			module.onPlayerChangeStateReligion(self, argsList)

		## Modular Python End
		## *******************

#FF: Added by Jean Elcard 03/01/2009 (State Names)
		pPlayer.updateStateNameType()
#FF: End Add

	def onPlayerGoldTrade(self, argsList):
		'Player Trades gold to another player'
		iFromPlayer, iToPlayer, iGoldAmount = argsList

	def onCityBuilt(self, argsList):
		'City Built'
		pCity 		= argsList[0]
		gc 			= CyGlobalContext()
		cf			= self.cf
		getInfoType	= gc.getInfoTypeForString
		game 		= CyGame()
		pPlot		= pCity.plot()
		iOwner		= pCity.getOwner()
		iSouth 		= DirectionTypes.DIRECTION_SOUTH
		iNoAI		= UnitAITypes.NO_UNITAI
		pPlayer		= gc.getPlayer(iOwner)
		Tech 		= self.Techs
		Speed 		= self.GameSpeeds
		eSpeed 		= game.getGameSpeedType()
		Civ			= self.Civilizations
		Rel			= self.Religions
		eCiv 		= pPlayer.getCivilizationType()
		Leader		= self.Leaders
		eLeader		= pPlayer.getLeaderType()
		Status		= self.LeaderStatus
		eStatus 	= pPlayer.getLeaderStatus()
		hasTrait	= pPlayer.hasTrait
		Trait		= self.Traits
		hasTrait	= pPlayer.hasTrait
		Building	= self.Buildings
		setNumB		= pCity.setNumRealBuilding
		iNumCities	= pPlayer.getNumCities()
		Unit		= self.Units["Generic"]
		Promo		= self.Promotions["Effects"]
		Race		= self.Promotions["Race"]
		Event		= self.EventTriggers
		iX = pCity.getX(); iY = pCity.getY()

		if getInfoType("MODULE_IMPORTANT_LEADERS")!=-1 and  hasTrait( getInfoType("TRAIT_TYRANT")):
			setNumB( getInfoType("BUILDING_TYRANT"), 1)

		if eLeader == getInfoType("LEADER_SAUROS") and eCiv== getInfoType("CIVILIZATION_CLAN_OF_EMBERS"):
			pCity.setCityClass(getInfoType("CITYCLASS_SAUROS_CLAN"))
		if eLeader == getInfoType("LEADER_SAUROS") and eCiv== getInfoType("CIVILIZATION_CUALLI"):
			pCity.setCityClass(getInfoType("CITYCLASS_SAUROS_CUALLI"))
		if hasTrait( Trait["Imperialist"]):
			iCulture = 10
			if   eSpeed == Speed["Marathon"]:	iCulture = iCulture * 3
			elif eSpeed == Speed["Epic"]:	   	iCulture = iCulture * 3 / 2
			elif eSpeed == Speed["Quick"]:	   	iCulture = iCulture / 3 * 2
			pCity.changeCulture(iOwner, iCulture, True)
		elif hasTrait( Trait["Hydromancer 1"]): # add water mana in Lorelei capital
			if pCity.isCapital():
				setNumB(Building["Water Mana"], 1)
		elif getInfoType("MODULE_CHUREL")!=-1 and hasTrait(Trait["Graveleech 1"]):
			if pCity.isCapital():
				setNumB(Building["Death Mana"], 1)			
		elif hasTrait( Trait["Necromancer 1"]): # add death mana in Naxus and Churel capital
			if pCity.isCapital():
				setNumB(Building["Death Mana"], 1)
		elif hasTrait( gc.getInfoTypeForString("TRAIT_AMBITIOUS")): # add Mind mana in Kahd Capital
			if pCity.isCapital():
				setNumB(gc.getInfoTypeForString("BUILDING_MANA_MIND"), 1)
		# EmergentLeaders: add Nightmare in Rigmora capital	
		elif getInfoType("MODULE_EMERGENT_LEADERS")!=-1 and hasTrait( Trait["Incorporeal 1"]):
			if pCity.isCapital():
				setNumB(Building["Nightmare"], 1)		

		#if eStatus == Status["Important"] and not hasTrait( Trait["Expansive"]):
		#	if iNumCities > 7:
		#		if game.getSorenRandNum(100, "Bob") <= 20:
		#			pPlayer.initTriggeredData( Event["Expansive"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		if pPlot.getBonusType(-1) == self.Mana["Mana"]:
			pPlot.setBonusType(-1)

		if eCiv == Civ["Infernal"]:
			setNumB( Building["Demonic Citizens"], 1)
			pCity.setPopulation(3)
			if game.countKnownTechNumTeams( Tech["Infernal Pact"]) > 0:
				pCity.setHasReligion( Rel["Ashen Veil"], True, True, True)
				setNumB( Building["Elder Council"], 1)
				setNumB( Building["Barracks"], 		1)
				setNumB( Building["Obsidian Gate"], 1)
				setNumB( Building["Forge"], 		1)
				setNumB( Building["Mage Guild"], 	1)

		elif eCiv == Civ["Austrin"]:
			setNumB( Building["Austrin Settlement"], 1)

		elif eCiv == Civ["Balseraphs"]:
			pCity.setHasCorporation( self.Corporations["Masquerade"], True, False, False)

		elif eCiv == Civ["Barbarian (Orc)"]:
			eEra 		= game.getStartEra()
			pTeam 		= gc.getTeam(gc.getPlayer(gc.getORC_PLAYER()).getTeam())
			iUnit 		= Unit["Warrior"]
			Era 		= self.Eras
			isHasTech	= pTeam.isHasTech
			if (isHasTech( Tech["Bronze Working"]) or eEra > Era["Ancient"]):
				iUnit 	= Unit["Axeman"]
			if (isHasTech( Tech["Iron Working"]) or eEra > Era["Classical"]):
				iUnit 	= Unit["Champion"]
			newUnit 	= pPlayer.initUnit(iUnit, iX, iY, iNoAI, iSouth)
			newUnit.setHasPromotion( Race["Orcish"], True)

			iUnit = Unit["Archer"]
			if (isHasTech( Tech["Bowyers"]) or eEra > Era["Classical"]):
				iUnit 	= Unit["Longbowman"]
			newUnit2 	= pPlayer.initUnit(iUnit, iX, iY, iNoAI, iSouth)
			newUnit3 	= pPlayer.initUnit(iUnit, iX, iY, iNoAI, iSouth)
			newUnit2.setHasPromotion( Race["Orcish"], True)
			newUnit3.setHasPromotion( Race["Orcish"], True)
			if ((not isHasTech( Tech["Archery"])) or eEra == Era["Ancient"]):
				newUnit2.setHasPromotion( Promo["Weak"], True)
				newUnit3.setHasPromotion( Promo["Weak"], True)

		# D'tesh Feature converter - TODO Ronkhar softcode this
		elif eCiv == Civ["D'Tesh"]:
			# big animals (--> nightmare or ash)
			resourcesPopup = ('BONUS_BISON','BONUS_CAMEL', 'BONUS_COW', 'BONUS_HORSE')
			# other living resources (--> ash)
			resourcesAlive = ('BONUS_BANANA','BONUS_CORN','BONUS_COTTON','BONUS_DEER','BONUS_DEER_ARCTIC','BONUS_DYE','BONUS_FUR','BONUS_GULAGARM','BONUS_INCENSE','BONUS_IVORY','BONUS_MUSHROOMS','BONUS_PIG','BONUS_RAZORWEED','BONUS_REAGENTS','BONUS_RICE','BONUS_SHEEP','BONUS_SILK','BONUS_SUGAR','BONUS_TOAD','BONUS_WHEAT','BONUS_WINE')
			# get bonus on city tile
			iBonus = pPlot.getBonusType(TeamTypes.NO_TEAM) # integer (for example 4) TODO CHECK IF TeamTypes.NO_TEAM is the correct option
			if iBonus != -1: # if there is a bonus
				sBonus = gc.getBonusInfo(iBonus).getType() # string (for example "BONUS_CAMEL")
				if sBonus == 'BONUS_NIGHTMARE':
					if gc.getPlayer(iOwner).isHuman():
						popupInfo = CyPopupInfo()
						popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
						popupInfo.setText(CyTranslator().getText("TXT_KEY_DTESH_FIND_NIGHTMARE",()))
						popupInfo.setData1(pCity.getID())
						popupInfo.setData2(iOwner)
						popupInfo.setData3(122) # onModNetMessage id
						popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_DTESH_FIND_NIGHTMARE_KEEP",()),"")
						#popupInfo.addPythonButton(CyTranslator().getText("TXT_Dtesh_keep_nightmares", ()), "") # TODO Ronkhar
						popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_DTESH_FIND_NIGHTMARE_BURN",()),"")
						#popupInfo.addPythonButton(CyTranslator().getText("TXT_Dtesh_convert_to_ashes", ()), "")
						popupInfo.setOnClickedPythonCallback("passToModNetMessage")
						popupInfo.addPopup(iOwner)
					else: # the AI is basic --> always ash (could be upgraded: if already have nightmare, then ash, else nightmare)
						pPlot.setBonusType(gc.getInfoTypeForString('BONUS_ASH'))
				elif sBonus in resourcesPopup:
					if pPlayer.isHasTech(Tech["Animal Husbandry"]): # tech reveals horses and nightmare
						if gc.getPlayer(iOwner).isHuman(): # then popup(nightmare OR ash)
							popupInfo = CyPopupInfo()
							popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON)
							popupInfo.setText(CyTranslator().getText("TXT_KEY_DTESH_FIND_HORSE",()))
							popupInfo.setData1(pCity.getID())
							popupInfo.setData2(iOwner)
							popupInfo.setData3(121) # onModNetMessage id
							popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_DTESH_FIND_HORSE_NIGHTMARE",()),"")
							popupInfo.addPythonButton(CyTranslator().getText("TXT_KEY_DTESH_FIND_HORSE_BURN",()),"")
							popupInfo.setOnClickedPythonCallback("passToModNetMessage")
							popupInfo.addPopup(iOwner)
						else: # the AI is basic --> always ash
							pPlot.setBonusType(gc.getInfoTypeForString('BONUS_ASH'))
					else: # has not Tech[" Animal Husbandry"] --> always ash
						pPlot.setBonusType(gc.getInfoTypeForString('BONUS_ASH')) # TODO if player, add popup to tell him he gained 1 infused ash
				elif sBonus in resourcesAlive: # --> always ash
					pPlot.setBonusType(gc.getInfoTypeForString('BONUS_ASH')) # TODO if player, add popup to tell him he gained 1 infused ash

#FF: Added by Jean Elcard 03/01/2009 (State Names)
		pPlayer.updateStateNameType()
#FF: End Add

		if eLeader == Leader["Risen Emperor"]:
			setNumB( Building["Emperors Mark"], 1)

		if game.getWBMapScript():
			sf.onCityBuilt(pCity)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityBuilt']:
			module.onCityBuilt(self, argsList)

		## Modular Python End
		## *******************



		if pCity.getOwner() == game.getActivePlayer() and game.getAIAutoPlay() == 0:
			self.__eventEditCityNameBegin(pCity, False)
	##	CvUtil.pyPrint('City Built Event: %s' %(pCity.getName()))

	def onCityRazed(self, argsList):
		'City Razed'
		city, iPlayer 	= argsList
		gc 				= CyGlobalContext()
		cf				= self.cf
		game 			= CyGame()
		iOwner 			= city.findHighestCulture()
		iOriginalOwner 	= city.getOriginalOwner()
		getPlayer 		= gc.getPlayer
		pPlayer 		= getPlayer(iPlayer) # conqueror
		iPopulation 	= city.getPopulation()
		iNewOwner 		= city.getOwner() # duplicate of iPlayer
		iOriginalAlignment = getPlayer(iOriginalOwner).getAlignment()
		pPlot = city.plot()
		iX = city.getX(); iY = city.getY()
		eCiv 			= getPlayer(iOriginalOwner).getCivilizationType()
		eNewOwnerCiv	= getPlayer(iNewOwner).getCivilizationType()
		getCivActive 	= game.getNumCivActive
		hasTrait	 	= pPlayer.hasTrait
		Civic			= self.Civics
		Civ				= self.Civilizations
		Unit			= self.Units
		Status			= self.LeaderStatus
		Trait			= self.Traits
		Event			= self.EventTriggers
		Tech			= self.Techs
		Alignment		= self.Alignments
		Building		= self.Buildings
		Infernal		= self.Units["Infernal"]
		Mercurian		= self.Units["Mercurian"]
		iNoAI 			= UnitAITypes.NO_UNITAI
		iSouth			= DirectionTypes.DIRECTION_SOUTH

		if (pPlayer.hasTrait(Trait["Scorched Earth"])):
			for iUnit in xrange(pPlot.getNumUnits()):
					pUnit = pPlot.getUnit(iUnit)
					if pUnit.getOwner()==iPlayer:
						pUnit.changeExperience(iPopulation, -1, False, False, False)
				
		# Minor Trait Criteria : Raiders
		#if (pPlayer.getLeaderStatus() == Status["Important"]) and not hasTrait(Trait["Raiders"]):
		#	if game.getSorenRandNum(100, "Bob") <= 10:
		#		pPlayer.initTriggeredData(Event["Raiders"], True, -1, -1, -1, -1, -1, -1, -1, -1, -1)

		iAngel 		= Mercurian["Angel"]
		iInfernal 	= Civ["Infernal"]
		iManes 		= Infernal["Manes"]
		iMercurians = Civ["Mercurians"]
		giftUnit = cf.giftUnit
		if game.countKnownTechNumTeams(Tech["Infernal Pact"]) > 0 and getCivActive(iInfernal) > 0:
			if iOriginalAlignment == Alignment["Evil"]:
				if eCiv != iInfernal:
					for i in xrange(iPopulation):
						giftUnit(iManes, iInfernal, 0, pPlot, iNewOwner)

			if iOriginalAlignment == Alignment["Neutral"]:
				for i in xrange((iPopulation / 4) + 1):
					giftUnit(iManes, iInfernal, 0, pPlot, iNewOwner)
					giftUnit(iManes, iInfernal, 0, pPlot, iNewOwner)

		if game.getBuildingClassCreatedCount(Building["Mercurian Gate"]) > 0 and getCivActive(iMercurians) > 0:
			if iOriginalAlignment == Alignment["Neutral"]:
				for i in xrange((iPopulation / 4) + 1):
					giftUnit(iAngel, iMercurians, 0, pPlot, iNewOwner)

			if iOriginalAlignment == Alignment["Good"]:
				for i in xrange((iPopulation / 2) + 1):
					giftUnit(iAngel, iMercurians, 0, pPlot, iNewOwner)

		if game.getWBMapScript():
			sf.onCityRazed(city, iPlayer)

# scions start - Gives Reborn when razing cities.  The function reducing the population of Scion conquests kicks in first.  Currently Reborn given = that population -1.  Requires Sorc. and Priestood.  It's been suggested that be changed to requiring the civic "Glory."
		iReborn  = Unit["Scions"]["Reborn"]
		pTeam 	 = gc.getTeam(pPlayer.getTeam())
		hasTech	 = pTeam.isHasTech
		initUnit = pPlayer.initUnit
		if eNewOwnerCiv == Civ["Scions"]:
			if hasTech(Tech["Sorcery"]) and hasTech(Tech["Priesthood"]):
				if(iPopulation-1)<1:
					CyInterface().addMessage(iNewOwner,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_REBORN_SPAWNED_RAZED", ()),'',1,'Art/Interface/Buttons/Units/Scions/reborn.dds',ColorTypes(8),iX,iY,True,True)
					spawnUnit = initUnit(iReborn, iX, iY, iNoAI, iSouth)
				if pPlayer.isCivic(Civic["God King"]):
					if (iPopulation - 1) >= 1:
						CyInterface().addMessage(iNewOwner,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_REBORN_SPAWNED_RAZED", ()),'',1,'Art/Interface/Buttons/Units/Scions/reborn.dds',ColorTypes(8),iX,iY,True,True)
					for i in xrange((iPopulation) - 1):
						spawnUnit = initUnit(iReborn, iX, iY, iNoAI, iSouth)
				else:
					if (iPopulation - 1) >= 1:
						CyInterface().addMessage(iNewOwner,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_REBORN_SPAWNED_RAZED", ()),'',1,'Art/Interface/Buttons/Units/Scions/reborn.dds',ColorTypes(8),iX,iY,True,True)
					for i in xrange((iPopulation) - 1):
						spawnUnit = initUnit(iReborn, iX, iY, iNoAI, iSouth)

# scions end
# Legion of Dtesh
		if eNewOwnerCiv == Civ["D'Tesh"]:
			spawnUnit = initUnit(Unit["D'Tesh"]["Vessel of D'tesh"], iX, iY, iNoAI, iSouth)
			for i in xrange((iPopulation * 3 / 4) + 1):
				spawnUnit = initUnit(Unit["D'Tesh"]["Slave"], iX, iY, iNoAI, iSouth)

# End Legion of Dtesh

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityRazed']:
			module.onCityRazed(self, argsList)

		## Modular Python End
		## *******************

		CvUtil.pyPrint("City Razed Event: %s" %(city.getName(),))

	def onCityAcquired(self, argsList): # triggered whenever a city is captured (before the player chooses to keep or raze)
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'City Acquired'
		iPreviousOwner,iNewOwner,pCity,bConquest,bTrade = argsList
		gc 			= CyGlobalContext()
		cf			= self.cf
		game 		= CyGame()
		map 		= CyMap()
		getInfoType			= gc.getInfoTypeForString
		getPlayer 	= gc.getPlayer
#Scions Start - extra reduction of Scions-acquired cities.  Use of a decimal seems to break it.
		pPlayer 	= getPlayer(iNewOwner)
		eLeader		= pPlayer.getLeaderType()
		hasTrait 	= pPlayer.hasTrait
		pPlot 		= pCity.plot()
		setBuilding = pCity.setNumRealBuilding
		changePop	= pCity.changePopulation
		iCiv		= pPlayer.getCivilizationType()
		iCityOwner 	= pCity.getOwner()
		pCityOwner	= getPlayer(iCityOwner)
		Civ	 		= self.Civilizations
		Trait 		= self.Traits
		Leader 		= self.Leaders
		Civic 		= self.Civics
		Rel	 		= self.Religions
		Building 	= self.Buildings
		Unit		= self.Units
		iPop		= pCity.getPopulation()
		pPrevious	= getPlayer(iPreviousOwner)
		iNoAI 		= UnitAITypes.NO_UNITAI
		iSouth		= DirectionTypes.DIRECTION_SOUTH
		getPlot = map.plot
		
		if eLeader == getInfoType("LEADER_SAUROS") and iCiv== getInfoType("CIVILIZATION_CLAN_OF_EMBERS"):
			pCity.setCityClass(getInfoType("CITYCLASS_SAUROS_CLAN"))
		if eLeader == getInfoType("LEADER_SAUROS") and iCiv== getInfoType("CIVILIZATION_CUALLI"):
			pCity.setCityClass(getInfoType("CITYCLASS_SAUROS_CUALLI"))
		
	#	if bConquest:
	#		if hasTrait(getInfoType('TRAIT_SCORCHED_EARTH')):
	#			pPlayer.raze(pCity)
	#			return
				
		if hasTrait(Trait["Slaver"]):
			initUnit 	= pPlayer.initUnit
			iSlave 		= Unit["Generic"]["Slave"]
			pTeam 		= gc.getTeam(pPlayer.getTeam())
			iSlavePop 	= iPop / 2
			changePop(-iSlavePop)
			for i in xrange(iPop / 2):
				spawnUnit = initUnit(iSlave, pCity.getX(), pCity.getY(), iNoAI, iSouth)

		if pCityOwner.getCivilizationType() == Civ["Scions"] and pCityOwner.getLeaderType() != Leader["Koun"]:
			if pCityOwner.isCivic(Civic["God King"]):
				iBCPop = iPop * 10
				iBCMod = iBCPop / 16
				changePop(-iBCMod)
			else:
				iBCPop = iPop * 10
				iBCMod = iBCPop / 12
				changePop(-iBCMod)

		if pCityOwner.getCivilizationType() == Civ["D'Tesh"]:
			iBCPop = iPop * 10
			iBCMod = iBCPop / 30
			changePop(-iBCMod)

		if getPlayer(pCity.getPreviousOwner()).getCivilizationType() == Civ["Scions"]:
			iBCPop = iPop * 10
			iBCMod = iBCPop / 12
			changePop(-iBCMod)
#Scions End

		setBuilding(Building["Demonic Citizens"], 0)
		setBuilding(Building["Austrin Settlement"], 0)

		if iCiv == Civ["Infernal"]:
			setBuilding(Building["Demonic Citizens"], 1)
			pCity.setHasReligion(Rel["Order"], False, True, True)
			if game.countKnownTechNumTeams(self.Techs["Infernal Pact"]) > 0:
				pCity.setHasReligion(Rel["Ashen Veil"], True, True, True)
				setBuilding(Building["Elder Council"], 1)
				setBuilding(Building["Barracks"], 1)
				setBuilding(Building["Obsidian Gate"], 1)
				setBuilding(Building["Forge"], 1)
				setBuilding(Building["Mage Guild"], 1)


		if iCiv == Civ["Austrin"]:
			setBuilding(Building["Austrin Settlement"], 1)

		iPrevCiv = pPrevious.getCivilizationType()
		if (iPrevCiv == Civ["Infernal"]):
			setBuilding(Building["Obsidian Gate"], 0)

		if(iPrevCiv==Civ["Sidar"] or pCity.getNumRealBuilding(getInfoType('BUILDING_HIDDEN_CITY')) > 0):
			blocked = (getInfoType('FEATURE_VOLCANO'), getInfoType('FEATURE_VOLCANO'))

		#	pCity.plot().setMistChangeTimer(scale(6))
		#	pCity.plot().setMistChangeTemp(0)
			pCity.setNumRealBuilding(getInfoType('BUILDING_HIDDEN_CITY'), 0)

		#	for iiX,iiY in RANGE1:
		#		pPlot = getPlot(pCity.getX()+iiX,pCity.getY()+iiY)
		#		if pPlot.isCity(): continue
		#		if pPlot.isPeak(): continue
		#		if pPlot.getFeatureType() in blocked: continue
		#		pPlot.setMistChangeTemp(0)
		#		pPlot.setMistChangeTimer(scale(6))
#
#			for iiX,iiY in BFC2:
#				pPlot = getPlot(pCity.getX()+iiX,pCity.getY()+iiY)
#				if pPlot.isCity(): continue
#				if pPlot.isPeak(): continue
#				if pPlot.getFeatureType() in blocked: continue

#				pPlot.setMistChangeTemp(0)
#				pPlot.setMistChangeTimer(scale(3))
				
		if game.getWBMapScript():
			sf.onCityAcquired(iPreviousOwner, iNewOwner, pCity, bConquest, bTrade)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityAcquired']:
			module.onCityAcquired(self, argsList)

		## Modular Python End
		## *******************


		CvUtil.pyPrint('City Acquired Event: %s' %(pCity.getName()))

	def onCityAcquiredAndKept(self, argsList):
		'City Acquired and Kept'
		iOwner,pCity= argsList
		gc 			= CyGlobalContext()
		game 		= CyGame()
		pPlayer 	= gc.getPlayer(iOwner)
		Status 		= self.LeaderStatus

		#Functions added here tend to cause OOS issues

#FF: Added by Jean Elcard 03/01/2009 (State Names)
		pPlayer.updateStateNameType()
#FF: End Add

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityAcquiredAndKept']:
			module.onCityAcquiredAndKept(self, argsList)

		## Modular Python End
		## *******************

		CvUtil.pyPrint('City Acquired and Kept Event: %s' %(pCity.getName()))

	def onCityLost(self, argsList):
		'City Lost'
		city = argsList[0]
		player = PyPlayer(city.getOwner())

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityLost']:
			module.onCityLost(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_CITYLOST):
			return
		CvUtil.pyPrint('City %s was lost by Player %d Civilization %s'
			%(city.getName(), player.getID(), player.getCivilizationName()))

	def onCultureExpansion(self, argsList):
	## Platy Builder ##
		if CyGame().GetWorldBuilderMode() and not CvPlatyBuilderScreen.bPython: return
	## Platy Builder ##
		'City Culture Expansion'
		pCity = argsList[0]
		iPlayer = argsList[1]
	##	CvUtil.pyPrint("City %s's culture has expanded" %(pCity.getName(),))

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCultureExpansion']:
			module.onCultureExpansion(self, argsList)

		## Modular Python End
		## *******************

	def onCityGrowth(self, argsList):
		'City Population Growth'
		pCity = argsList[0]
		iPlayer = argsList[1]
		##CvUtil.pyPrint("%s has grown" %(pCity.getName(),))

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityGrowth']:
			module.onCityGrowth(self, argsList)

		## Modular Python End
		## *******************

	def onCityDoTurn(self, argsList):
		'City Production'
		pCity = argsList[0]
		iPlayer = argsList[1]

		gc 					= CyGlobalContext()
		cf					= self.cf
		getInfoType			= gc.getInfoTypeForString
		game 				= CyGame()
		map 				= CyMap()
		getPlot 			= map.plot
		isHasReligion 		= pCity.isHasReligion
		setHasReligion 		= pCity.setHasReligion
		pPlot 				= pCity.plot()
		iPlayer 			= pCity.getOwner()
		getPlayer 			= gc.getPlayer
		pPlayer 			= getPlayer(iPlayer)
		randNum 			= game.getSorenRandNum
		hasTrait 			= pPlayer.hasTrait
		pyPlayer 			= PyPlayer(iPlayer)
		Speed				= self.GameSpeeds
		iGameSpeed 			= game.getGameSpeedType()
		numB 				= pCity.getNumBuilding
		countNumB 			= pPlayer.countNumBuildings
		globalCounter 		= game.getGlobalCounter()
		setB				= pCity.setNumRealBuilding
		getBuilding 		= gc.getBuildingInfo
		getBClassCount  	= pPlayer.getBuildingClassCount
		iCiv 				= pPlayer.getCivilizationType()
		getUnitCCount 		= pPlayer.getUnitClassCount
		message				= CyInterface().addMessage
		initUnit 			= pPlayer.initUnit
		Building			= self.Buildings
		Define				= self.Defines
		Civ					= self.Civilizations
		Rel					= self.Religions
		Trait				= self.Traits
		Civic				= self.Civics
		Unit				= self.Units
		Promo				= self.Promotions["Effects"]
		Race				= self.Promotions["Race"]
		iNoAI 				= UnitAITypes.NO_UNITAI
		iSouth				= DirectionTypes.DIRECTION_SOUTH
		iNorth				= DirectionTypes.DIRECTION_NORTH
		getNumAvailBonuses 	= pPlayer.getNumAvailableBonuses
		iX = pCity.getX(); iY = pCity.getY()

		if numB(getInfoType("BUILDING_PIXIE_GARDEN")>0):
			if (pPlot.getNumUnits())>0:
				if randNum(1000,"Pixie")<2:
					pUnit = pPlot.getUnit(0)
					if ( pUnit.isAlive() and not pUnit.isHasPromotion(getInfoType("PROMOTION_PIXIE_COMPANION"))):
						pUnit.setHasPromotion(getInfoType("PROMOTION_PIXIE_COMPANION"),True)
						message(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_PIXIE_JOIN",()),'AS2D_TECH_DING',1,'Art/units/spawns/fairy/fairy.dds',ColorTypes(8),iX,iY,True,True)

#scions start - Gives chance to remove some of Pelemoc's effects.
		if numB( Building["Riot and Sedition"]) > 0:
			if randNum(100, "Spell expiration") < 16: setB( Building["Riot and Sedition"], 0)

		if numB( Building["Poison Words"]) > 0:
			if randNum(100, "Spell expiration") < 5: setB( Building["Poison Words"], 0)

		if numB( Building["Hall of Mirrors"]) > 0:
			if randNum(100, "Hall of Mirrors") <= 100:
				pUnit = -1
				iX = iX
				iY = iY
				pTeam = gc.getTeam(pPlayer.getTeam())
				for iiX,iiY in RANGE1:
					pPlot2 = getPlot(iX+iiX,iY+iiY)
					if pPlot2.isVisibleEnemyUnit(iPlayer):
						getUnit = pPlot2.getUnit
						for i in xrange(pPlot2.getNumUnits()):
							pUnit2 = getUnit(i)
							if pTeam.isAtWar(pUnit2.getTeam()):
								pUnit = pUnit2
				if pUnit != -1:
					newUnit = initUnit(pUnit.getUnitType(), iX, iY, iNoAI, iNorth)
					newUnit.setHasPromotion( Race["Illusion"], True)
					if pPlayer.hasTrait( Trait["Summoner"]):
						newUnit.setDuration(5)
					else:
						newUnit.setDuration(3)

		if numB( Building["Eyes and Ears"]) > 0:
			pTeam = gc.getTeam(pPlayer.getTeam())
			listTeams = []
			for iPlayer2 in xrange(gc.getMAX_PLAYERS()):
				pPlayer2 = gc.getPlayer(iPlayer2)
				if (pPlayer2.isAlive() and iPlayer2 != iPlayer):
					iTeam2 = pPlayer2.getTeam()
					if pTeam.isOpenBorders(iTeam2):
						listTeams.append(gc.getTeam(iTeam2))
			if len(listTeams) >= 3:
				setTech 	= pTeam.setHasTech
				canResearch = pPlayer.canEverResearch
				for iTech in xrange(gc.getNumTechInfos()):
					if (canResearch(iTech)):
						if pTeam.isHasTech(iTech) == False:
							iCount = 0
							for i in xrange(len(listTeams)):
								if listTeams[i].isHasTech(iTech):
									iCount = iCount + 1
							if iCount >= 3:
								setTech(iTech, True, iPlayer, False, True)
								message(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_EYES_AND_EARS_NETWORK_FREE_TECH",()),'AS2D_TECH_DING',1,'Art/Interface/Buttons/Buildings/Eyesandearsnetwork.dds',ColorTypes(8),iX,iY,True,True)

		if numB( Building["Planar Gate"]) > 0: # sheaim spawn creatures
			cf.doCityTurnPlanarGate(iPlayer, pCity)

		if numB( Building["Memorial Refugee"]) > 0 or numB( Building["Dwelling of Refuge"]) > 0: # grigori spawn refugees
			cf.doCityTurnMemorial(iPlayer, pCity)

# FF: KAHDI GATES
### If you have a gate, you can summon gate creatures
### Maximum number of creatures empire-wide is based on number of Gates, Repositories, Meditation Halls and Mage Guilds.

		if numB( Building["Kahdi Vault Gate"]) > 0:
			iMax = 1
			iMult = 1

			if hasTrait( gc.getInfoTypeForString("TRAIT_KAHD_OGHMA")):
				iMult = 3
				iMax = 1.5  # Yes, I know that 1.5 isn't an integer but never mind...

			if numB( Building["Library"]) > 0: iMult += 0.5

			if randNum(10000, "Planar Gate") <= (Define["Planar Gate"] * iMult):
				listUnits = []
				iGates 			= countNumB( Building["Kahdi Vault Gate"])
				iLibraries 		= countNumB( Building["Library"])
				iMedHalls 		= countNumB( Building["School of Govannon"])
				iGreatLibrary 	= countNumB( Building["The Great Library"]) * 4
				iMageGuild 		= countNumB( Building["Wizards Hall"])
				iManaCount	 	= cf.countMana(pPlayer)

				iMax = iMax *  (iGates + iLibraries + iMedHalls + iGreatLibrary + iMageGuild)

				### Gnoslings always available, others require a building
				UnitClass = self.UnitClasses
				Kahdi 	= self.Units["Kahdi"]
				Summons 	= self.Units["Summons"]
				Mana 	= self.Mana
				if getUnitCCount( UnitClass["Gnossling"]) < (iMax/2):
					listUnits.append( Kahdi["Gnosling"])
				if numB(Building["Wizards Hall"]) > 0:
					if getUnitCCount( UnitClass["Thade"]) < (iMax/3):
						listUnits.append( Kahdi["Thade"])
				if numB(Building["School of Govannon"]) > 0:
					iNum = getNumAvailBonuses( Mana["Metamagic"] )
					if iNum > 0:
						if getUnitCCount( UnitClass["Djinn"]) < (iMax/4)*iNum :
							listUnits.append( Summons["Djinn"])

					iNum = getNumAvailBonuses( Mana["Fire"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Fire Elemental"]) < (iMax/6)*iNum :
							listUnits.append( Summons["Fire Elemental"])

					iNum = getNumAvailBonuses( Mana["Air"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Air Elemental"]) < (iMax/6)*iNum :
							listUnits.append( Summons["Air Elemental"])

					iNum = getNumAvailBonuses( Mana["Death"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Spectre"]) < (iMax/4)*iNum :
							listUnits.append( Summons["Spectre"])

					iNum = getNumAvailBonuses( Mana["Body"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Flesh Golem"]) < (iMax/6)*iNum :
							listUnits.append( Summons["Flesh Golem"])

					iNum = getNumAvailBonuses( Mana["Entropy"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Pit Beast"]) < (iMax/4)*iNum :
							listUnits.append( Summons["Pit Beast"])

					iNum = getNumAvailBonuses( Mana["Ice"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Ice Elemental"]) < (iMax/4)*iNum :
							listUnits.append( Summons["Ice Elemental"])

					iNum = getNumAvailBonuses( Mana["Law"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Einherjar"]) < (iMax/4)*iNum :
							listUnits.append( Summons["Einherjar"])

					iNum = getNumAvailBonuses( Mana["Shadow"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Mistform"]) < (iMax/8)*iNum :
							listUnits.append( Summons["Mistform"])

					iNum = getNumAvailBonuses( Mana["Sun"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Aurealis"]) < (iMax/6)*iNum :
							listUnits.append( Summons["Aurealis"])

					iNum = getNumAvailBonuses( Mana["Water"])
					if iNum > 0:
						if getUnitCCount( UnitClass["Water Elemental"]) < (iMax/6)*iNum :
							listUnits.append( Summons["Water Elemental"])

				#Psions
				if  hasTrait( gc.getInfoTypeForString("TRAIT_KAHD_MAMMON")):
					if getUnitCCount( UnitClass["Psion"] ) < 1 + (iMax/10):
						listUnits.append( Kahdi["Psion"])

				if len(listUnits) > 0:
					iUnit = listUnits[randNum(len(listUnits), "Kahdi Gate")]
					newUnit = initUnit(iUnit, iX, iY, iNoAI, iNorth)
					message(iPlayer,True,25,CyTranslator().getText("TXT_KEY_MESSAGE_KAHDI_GATE",()),'AS2D_DISCOVERBONUS',1,gc.getUnitInfo(newUnit.getUnitType()).getButton(),ColorTypes(8),iX,iY,True,True)
					if iUnit == Kahdi["Thade"]:
						promotions = ['PROMOTION_AIR1','PROMOTION_BODY1','PROMOTION_EARTH1','PROMOTION_ENCHANTMENT1','PROMOTION_LAW1','PROMOTION_LIFE1','PROMOTION_MIND1','PROMOTION_NATURE1','PROMOTION_SPIRIT1','PROMOTION_WATER1', 'PROMOTION_AIR2', 'PROMOTION_FIRE2', 'PROMOTION_EARTH2', 'PROMOTION_NATURE2', 'PROMOTION_LAW2']
						newUnit.setLevel(4)
						newUnit.setExperienceTimes100(1400, -1)
						setPromo = newUnit.setHasPromotion
						for i in promotions:
							if randNum(5, "Thade Free Promotions") == 1:
								setPromo(getInfoType(i), True)


					# Redeemed Kahd summons are strong
					if hasTrait( gc.getInfoTypeForString("TRAIT_KAHD_OGHMA")):
						newUnit.setHasPromotion( Promo["Strong"], True)
					# corrupted Psions are strong too
				#	if (hasTrait( gc.getInfoTypeForString("TRAIT_KAHD_MAMMON")) and iUnit==Kahdi["Psion"]):
				#		newUnit.setHasPromotion( getInfoType("PROMOTION_COMMAND1", True))
				#		newUnit.setHasPromotion( getInfoType("PROMOTION_COMMAND2", True))
				#		newUnit.setHasPromotion( getInfoType("PROMOTION_COMMAND3", True))
					

# FF: End

# 	Doviello
		elif iCiv == Civ["Doviello"]:
			cf.doCityTurnDoviello(iPlayer, pCity)
# 	Infernals
		elif iCiv == Civ["Infernal"]:
			if isHasReligion(Rel["Order"]):
				setHasReligion(Rel["Order"], False, True, True)
			if game.countKnownTechNumTeams(getInfoType('TECH_INFERNAL_PACT')) > 0:
				if isHasReligion(Rel["Ashen Veil"]) == False:
					setHasReligion(Rel["Ashen Veil"], True, True, True)

# 	Mercurians
		elif iCiv == Civ["Mercurians"]:
			if isHasReligion(Rel["Ashen Veil"]):
				setHasReligion(Rel["Ashen Veil"], False, True, True)

		if numB(Building["Shrine of Sirona"]) > 0:
			pPlayer.setFeatAccomplished(FeatTypes.FEAT_HEAL_UNIT_PER_TURN, True)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityDoTurn']:
			module.onCityDoTurn(self, argsList)

		## Modular Python End
		## *******************

		CvAdvisorUtils.cityAdvise(pCity, iPlayer)

	def onCityBuildingUnit(self, argsList):
		'City begins building a unit'
		pCity = argsList[0]
		iUnitType = argsList[1]
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityBuildingUnit']:
			module.onCityBuildingUnit(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_CITYBUILDING):
			return
		CvUtil.pyPrint("%s has begun building a %s" %(pCity.getName(),gc.getUnitInfo(iUnitType).getDescription()))

	def onCityBuildingBuilding(self, argsList):
		'City begins building a Building'
		pCity = argsList[0]
		iBuildingType = argsList[1]
		gc = CyGlobalContext()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityBuildingBuilding']:
			module.onCityBuildingBuilding(self, argsList)

		## Modular Python End
		## *******************

		if (not self.__LOG_CITYBUILDING):
			return
		CvUtil.pyPrint("%s has begun building a %s" %(pCity.getName(),gc.getBuildingInfo(iBuildingType).getDescription()))

	def onCityRename(self, argsList):
		'City is renamed'
		pCity = argsList[0]
		game = CyGame()
		if (pCity.getOwner() == game.getActivePlayer()):
			self.__eventEditCityNameBegin(pCity, True)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityRename']:
			module.onCityRename(self, argsList)

		## Modular Python End
		## *******************

	def onCityHurry(self, argsList):
		'City is renamed'
		pCity = argsList[0]
		iHurryType = argsList[1]

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onCityHurry']:
			module.onCityHurry(self, argsList)

		## Modular Python End
		## *******************

	def onVictory(self, argsList):
		'Victory'
		iTeam, iVic = argsList
		gc = CyGlobalContext()
		game 		= CyGame()
		getPlayer 	= gc.getPlayer

		if (iVic >= 0 and iVic < gc.getNumVictoryInfos()):
			trophy 		= game.changeTrophyValue
			Option		= self.GameOptions
			Civ 		= self.Civilizations
			Victory		= self.Victories
			for iPlayer in xrange(gc.getMAX_PLAYERS()):
				pPlayer = getPlayer(iPlayer)
				if pPlayer.isAlive() and pPlayer.isHuman() and pPlayer.getTeam() == iTeam:
					if game.getWBMapScript():
						sf.onVictory(iPlayer, iVic)
					else:
						iCiv = pPlayer.getCivilizationType()
						if   iCiv == Civ["Amurites"]:       trophy("TROPHY_VICTORY_AMURITES", 1)
						elif iCiv == Civ["Archos"]:         trophy("TROPHY_VICTORY_ARCHOS", 1)
						elif iCiv == Civ["Austrin"]:        trophy("TROPHY_VICTORY_AUSTRIN", 1)
						elif iCiv == Civ["Balseraphs"]:     trophy("TROPHY_VICTORY_BALSERAPHS", 1)
						elif iCiv == Civ["Bannor"]:         trophy("TROPHY_VICTORY_BANNOR", 1)
						elif iCiv == Civ["Calabim"]:        trophy("TROPHY_VICTORY_CALABIM", 1)
						elif iCiv == Civ["Chislev"]:        trophy("TROPHY_VICTORY_CHISLEV", 1)
						elif iCiv == Civ["Clan of Embers"]: trophy("TROPHY_VICTORY_CLAN_OF_EMBERS", 1)
						elif iCiv == Civ["Cualli"]:         trophy("TROPHY_VICTORY_CUALLI", 1)
						elif iCiv == Civ["Doviello"]:       trophy("TROPHY_VICTORY_DOVIELLO", 1)
						elif iCiv == Civ["D'Tesh"]:         trophy("TROPHY_VICTORY_DTESH", 1)
						elif iCiv == Civ["Dural"]:          trophy("TROPHY_VICTORY_DURAL", 1)
						elif iCiv == Civ["Elohim"]:         trophy("TROPHY_VICTORY_ELOHIM", 1)
						elif iCiv == Civ["Grigori"]:        trophy("TROPHY_VICTORY_GRIGORI", 1)
						elif iCiv == Civ["Hippus"]:         trophy("TROPHY_VICTORY_HIPPUS", 1)
						elif iCiv == Civ["Illians"]:        trophy("TROPHY_VICTORY_ILLIANS", 1)
						elif iCiv == Civ["Infernal"]:       trophy("TROPHY_VICTORY_INFERNAL", 1)
						elif iCiv == Civ["Jotnar"]:         trophy("TROPHY_VICTORY_JOTNAR", 1)
						elif iCiv == Civ["Khazad"]:         trophy("TROPHY_VICTORY_KHAZAD", 1)
						elif iCiv == Civ["Kuriotates"]:     trophy("TROPHY_VICTORY_KURIOTATES", 1)
						elif iCiv == Civ["Lanun"]:          trophy("TROPHY_VICTORY_LANUN", 1)
						elif iCiv == Civ["Ljosalfar"]:      trophy("TROPHY_VICTORY_LJOSALFAR", 1)
						elif iCiv == Civ["Luchuirp"]:       trophy("TROPHY_VICTORY_LUCHUIRP", 1)
						elif iCiv == Civ["Malakim"]:        trophy("TROPHY_VICTORY_MALAKIM", 1)
						elif iCiv == Civ["Mazatl"]:         trophy("TROPHY_VICTORY_MAZATL", 1)
						elif iCiv == Civ["Mechanos"]:       trophy("TROPHY_VICTORY_MECHANOS", 1)
						elif iCiv == Civ["Mercurians"]:     trophy("TROPHY_VICTORY_MERCURIANS", 1)
						elif iCiv == Civ["Scions"]:         trophy("TROPHY_VICTORY_SCIONS", 1)
						elif iCiv == Civ["Sheaim"]:         trophy("TROPHY_VICTORY_SHEAIM", 1)
						elif iCiv == Civ["Sidar"]:          trophy("TROPHY_VICTORY_SIDAR", 1)
						elif iCiv == Civ["Svartalfar"]:     trophy("TROPHY_VICTORY_SVARTALFAR", 1)

						if   iVic == Victory["Altar"]: 		trophy("TROPHY_VICTORY_ALTAR_OF_THE_LUONNOTAR", 1)
						elif iVic == Victory["Conquest"]:	trophy("TROPHY_VICTORY_CONQUEST", 1)
						elif iVic == Victory["Cultural"]:	trophy("TROPHY_VICTORY_CULTURAL", 1)
						elif iVic == Victory["Domination"]:	trophy("TROPHY_VICTORY_DOMINATION", 1)
						elif iVic == Victory["Religious"]:	trophy("TROPHY_VICTORY_RELIGIOUS", 1)
						elif iVic == Victory["Score"]:		trophy("TROPHY_VICTORY_SCORE", 1)
						elif iVic == Victory["Time"]:		trophy("TROPHY_VICTORY_TIME", 1)
						elif iVic == Victory["Tower"]:		trophy("TROPHY_VICTORY_TOWER_OF_MASTERY", 1)

						if Option["Barbarian World"]: 		trophy("TROPHY_VICTORY_BARBARIAN_WORLD", 1)
						if Option["Cut Losers"]:			trophy("TROPHY_VICTORY_FINAL_FIVE", 1)
						if Option["High to Low"]:			trophy("TROPHY_VICTORY_HIGH_TO_LOW", 1)
						if Option["Increasing Difficulty"]:	trophy("TROPHY_VICTORY_INCREASING_DIFFICULTY", 1)

			victoryInfo = gc.getVictoryInfo(int(iVic))
			CvUtil.pyPrint("Victory!  Team %d achieves a %s victory"
				%(iTeam, victoryInfo.getDescription()))

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onVictory']:
			module.onVictory(self, argsList)

		## Modular Python End
		## *******************

	def onVassalState(self, argsList):
		'Vassal State'
		iMaster, iVassal, bVassal = argsList
		gc = CyGlobalContext()

		if (bVassal):
			CvUtil.pyPrint("Team %d becomes a Vassal State of Team %d"
				%(iVassal, iMaster))
		else:
			CvUtil.pyPrint("Team %d revolts and is no longer a Vassal State of Team %d"
				%(iVassal, iMaster))
		getPlayer = gc.getPlayer
#FF: Added by Jean Elcard 03/01/2009 (State Names)
		for iPlayer in xrange(gc.getMAX_PLAYERS()):
			pPlayer = getPlayer(iPlayer)
			if pPlayer.isAlive():
				if (pPlayer.getTeam() == iMaster) or (pPlayer.getTeam() == iVassal):
					print "Update State Name for %d." % iPlayer
					print "Vassal: %s" % gc.getTeam(pPlayer.getTeam()).isAVassal()
					pPlayer.updateStateNameType()
#FF: End Add

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onVassalState']:
			module.onVassalState(self, argsList)

		## Modular Python End
		## *******************

	def onGameUpdate(self, argsList):
		'sample generic event, called on each game turn slice'
		genericArgs = argsList[0][0]	# tuple of tuple of my args
		turnSlice = genericArgs[0]

		doDeferredCalls()

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onGameUpdate']:
			module.onGameUpdate(self, argsList)

		## Modular Python End
		## *******************

		# Added by Gerikes for OOS logging.
		if CyInterface().isOOSVisible():
			CyMessageControl().sendModNetMessage(CvUtil.AutoPlay, 0, -1, -1, -1)
			OOSLogger.doGameUpdate()
		# End added by Gerikes for OOS logging.

	def onMouseEvent(self, argsList):
		'mouse handler - returns 1 if the event was consumed'
		eventType,mx,my,px,py,interfaceConsumed,screens = argsList
		if ( px!=-1 and py!=-1 ):
			if ( eventType == self.EventLButtonDown ):
				if (self.bAllowCheats and self.bCtrl and self.bAlt and CyMap().plot(px,py).isCity() and not interfaceConsumed):
					# Launch Edit City Event
					self.beginEvent( CvUtil.EventEditCity, (px,py) )
					return 1

				elif (self.bAllowCheats and self.bCtrl and self.bShift and not interfaceConsumed):
					# Launch Place Object Event
					self.beginEvent( CvUtil.EventPlaceObject, (px, py) )
					return 1

		if ( eventType == self.EventBack ):
			return CvScreensInterface.handleBack(screens)
		elif ( eventType == self.EventForward ):
			return CvScreensInterface.handleForward(screens)

		## *******************
		## Modular Python: ANW 29-may-2010

		for module in command['onMouseEvent']:
			module.onMouseEvent(self, argsList)

		## Modular Python End
		## *******************

		return 0


#################### TRIGGERED EVENTS ##################

	def __eventEditCityNameBegin(self, city, bRename):
		popup = PyPopup.PyPopup(CvUtil.EventEditCityName, EventContextTypes.EVENTCONTEXT_ALL)
		popup.setUserData((city.getID(), bRename))
		popup.setHeaderString(localText.getText("TXT_KEY_NAME_CITY", ()))
		popup.setBodyString(localText.getText("TXT_KEY_SETTLE_NEW_CITY_NAME", ()))
		popup.createEditBox(city.getName())
		popup.setEditBoxMaxCharCount( 15 )
		popup.launch()

	def __eventEditCityNameApply(self, playerID, userData, popupReturn):
		'Edit City Name Event'
		iCityID = userData[0]
		bRename = userData[1]
		player = CyGlobalContext().getPlayer(playerID)
		city = player.getCity(iCityID)
		cityName = popupReturn.getEditBoxString(0)
		if (len(cityName) > 30):
			cityName = cityName[:30]
		city.setName(cityName, not bRename)

	def __eventEditCityBegin(self, argsList):
		'Edit City Event'
		px,py = argsList
		CvWBPopups.CvWBPopups().initEditCity(argsList)

	def __eventEditCityApply(self, playerID, userData, popupReturn):
		'Edit City Event Apply'
		if (getChtLvl() > 0):
			CvWBPopups.CvWBPopups().applyEditCity( (popupReturn, userData) )

	def __eventPlaceObjectBegin(self, argsList):
		'Place Object Event'
		CvDebugTools.CvDebugTools().initUnitPicker(argsList)

	def __eventPlaceObjectApply(self, playerID, userData, popupReturn):
		'Place Object Event Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyUnitPicker( (popupReturn, userData) )

	def __eventAwardTechsAndGoldBegin(self, argsList):
		'Award Techs & Gold Event'
		CvDebugTools.CvDebugTools().cheatTechs()

	def __eventAwardTechsAndGoldApply(self, playerID, netUserData, popupReturn):
		'Award Techs & Gold Event Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyTechCheat( (popupReturn) )

	def __eventShowWonderBegin(self, argsList):
		'Show Wonder Event'
		CvDebugTools.CvDebugTools().wonderMovie()

	def __eventShowWonderApply(self, playerID, netUserData, popupReturn):
		'Wonder Movie Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyWonderMovie( (popupReturn) )

	def __eventEditUnitNameBegin(self, argsList):
		pUnit = argsList
		popup = PyPopup.PyPopup(CvUtil.EventEditUnitName, EventContextTypes.EVENTCONTEXT_ALL)
		popup.setUserData((pUnit.getID(),))
		popup.setBodyString(localText.getText("TXT_KEY_RENAME_UNIT", ()))
		popup.createEditBox(pUnit.getNameNoDesc())
		popup.launch()

	def __eventEditUnitNameApply(self, playerID, userData, popupReturn):
		'Edit Unit Name Event'
		iUnitID = userData[0]
		unit = CyGlobalContext().getPlayer(playerID).getUnit(iUnitID)
		newName = popupReturn.getEditBoxString(0)
		if (len(newName) > 25):
			newName = newName[:25]
		unit.setName(newName)
		if CyGame().GetWorldBuilderMode():
			WBUnitScreen.WBUnitScreen(CvPlatyBuilderScreen.CvWorldBuilderScreen()).placeStats()
			WBUnitScreen.WBUnitScreen(CvPlatyBuilderScreen.CvWorldBuilderScreen()).placeCurrentUnit()	

	def __eventWBAllPlotsPopupBegin(self, argsList):
		CvScreensInterface.getWorldBuilderScreen().allPlotsCB()
		return

	def __eventWBAllPlotsPopupApply(self, playerID, userData, popupReturn):
		if (popupReturn.getButtonClicked() >= 0):
			CvScreensInterface.getWorldBuilderScreen().handleAllPlotsCB(popupReturn)
		return

	def __eventWBLandmarkPopupBegin(self, argsList):
		CvScreensInterface.getWorldBuilderScreen().setLandmarkCB("")
		#popup = PyPopup.PyPopup(CvUtil.EventWBLandmarkPopup, EventContextTypes.EVENTCONTEXT_ALL)
		#popup.createEditBox(localText.getText("TXT_KEY_WB_LANDMARK_START", ()))
		#popup.launch()
		return

#	def __eventWBLandmarkPopupApply(self, playerID, userData, popupReturn):
#		if (popupReturn.getEditBoxString(0)):
#			szLandmark = popupReturn.getEditBoxString(0)
#			if (len(szLandmark)):
#				CvScreensInterface.getWorldBuilderScreen().setLandmarkCB(szLandmark)
#		return

#	def __eventWBScriptPopupBegin(self, argsList):
#		popup = PyPopup.PyPopup(CvUtil.EventWBScriptPopup, EventContextTypes.EVENTCONTEXT_ALL)
#		popup.setHeaderString(localText.getText("TXT_KEY_WB_SCRIPT", ()))
#		popup.createEditBox(CvScreensInterface.getWorldBuilderScreen().getCurrentScript())
#		popup.launch()
#		return

	def __eventWBScriptPopupApply(self, playerID, userData, popupReturn):
		if (popupReturn.getEditBoxString(0)):
			szScriptName = popupReturn.getEditBoxString(0)
			CvScreensInterface.getWorldBuilderScreen().setScriptCB(szScriptName)
		return

	def __eventWBStartYearPopupBegin(self, argsList):
		popup = PyPopup.PyPopup(CvUtil.EventWBStartYearPopup, EventContextTypes.EVENTCONTEXT_ALL)
		popup.createSpinBox(0, "", game.getStartYear(), 1, 5000, -5000)
		popup.launch()
		return

	def __eventWBStartYearPopupApply(self, playerID, userData, popupReturn):
		iStartYear = popupReturn.getSpinnerWidgetValue(int(0))
		CvScreensInterface.getWorldBuilderScreen().setStartYearCB(iStartYear)
		return

	def __eventSetHasTraitBegin(self, argslist):
		return 0

	def __eventSetHasTraitApply(self, playerID, userData, popupReturn):
		iPlayer, iTrait, bHas = userData
		pPlayer = CyGlobalContext().getPlayer(iPlayer)
		if not gc.isNoCrash():
			pPlayer.setHasTrait(iTrait, bHas,-1,True,True)
		else:
			pPlayer.setHasTrait(iTrait, bHas)
		return 0

	def __eventSetTurnsAutoPlayBegin(self, argslist):
		return 0

	def __eventSetTurnsAutoPlayApply(self, playerID, userData, popupReturn):
		if popupReturn.getButtonClicked() == 0: # ok button
			sEditBoxContent = popupReturn.getEditBoxString(0)
			if sEditBoxContent.isdigit():
				iNumTurns = int(sEditBoxContent)
				# AI Autoplay Sounds by Grey Fox
				profile = CyUserProfile()
				SoundSettings["SOUND_MASTER_VOLUME"] 	= profile.getMasterVolume()
				SoundSettings["SOUND_SPEECH_VOLUME"] 	= profile.getSpeechVolume()
				SoundSettings["SOUND_MASTER_NO_SOUND"] 	= profile.isMasterNoSound()
				profile.setMasterNoSound(True)
				# End
				CyMessageControl().sendModNetMessage(CvUtil.AutoPlay, iNumTurns, -1, -1, -1)
		return 0

	def __eventSetUnitPerTileBegin(self, argslist):
		return 0

	def __eventSetUnitPerTileApply(self, playerID, userData, popupReturn):
		if (popupReturn.getButtonClicked() == 0 or popupReturn.getButtonClicked() == 1): # Okay/Lock buttons
			sEditBoxContent = popupReturn.getEditBoxString(0)
			if sEditBoxContent.isdigit():
				iNumUPT = int(sEditBoxContent)
				bLock = False
				if popupReturn.getButtonClicked() == 1:
					bLock = True
				CyMessageControl().sendModNetMessage(CvUtil.UPT, iNumUPT, bLock, -1, -1)
		return 0

## FfH Card Game: begin
	def __EventSelectSolmniumPlayerBegin(self):
		gc = CyGlobalContext()
		game = CyGame()
		iHUPlayer = game.getActivePlayer()
		getPlayer = gc.getPlayer
		getLeaderHeadInfo = gc.getLeaderHeadInfo

		if iHUPlayer == -1 : return 0
		if not cs.canStartGame(iHUPlayer) : return 0

		popup = PyPopup.PyPopup(CvUtil.EventSelectSolmniumPlayer, EventContextTypes.EVENTCONTEXT_ALL)

		sResText = CyUserProfile().getResolutionString(CyUserProfile().getResolution())
		sX, sY = sResText.split("x")
		iXRes = int(sX)
		iYRes = int(sY)

		iW = 620
		iH = 650

		popup.setSize(iW, iH)
		popup.setPosition((iXRes - iW) / 2, 30)

		lStates = []
		startMPGame = cs.getStartGameMPWith
		startAIGame = cs.getStartGameAIWith
		for iPlayer in xrange(gc.getMAX_CIV_PLAYERS()) :
			pPlayer = getPlayer(iPlayer)

			if pPlayer.isNone() : continue

			if pPlayer.isHuman() :
				lPlayerState = startMPGame(iHUPlayer, iPlayer)
				if lPlayerState[0][0] in ["No", "notMet"] : continue
				lStates.append([iPlayer, lPlayerState])
			else :
				lPlayerState = startAIGame(iHUPlayer, iPlayer)
				if lPlayerState[0][0] in ["No", "notMet"] : continue
				lStates.append([iPlayer, lPlayerState])

		lPlayerButtons = []

		popup.addDDS(CyArtFileMgr().getInterfaceArtInfo("SOMNIUM_POPUP_INTRO").getPath(), 0, 0, 512, 128)
		popup.addSeparator()
		#popup.setHeaderString(localText.getText("TXT_KEY_SOMNIUM_START", ()), CvUtil.FONT_CENTER_JUSTIFY)
		if len(lStates) == 0 :
			popup.setBodyString(localText.getText("TXT_KEY_SOMNIUM_NOONE_MET", ()))
			sText = u""
		else :
			#popup.setBodyString(localText.getText("TXT_KEY_SOMNIUM_PLAY_WITH", ()))
			popup.addSeparator()
			popup.addSeparator()

			sText = u""
			for iPlayer, lPlayerState in lStates :
				pPlayer 		= getPlayer(iPlayer)
				sPlayerName 	= pPlayer.getName()
				eType 			= pPlayer.getLeaderType()
				getMemory 		= getLeaderHeadInfo(eType).getMemoryAttitudePercent
				iPositiveChange = getMemory(MemoryTypes.MEMORY_SOMNIUM_POSITIVE) / 100
				iNegativeChange = getMemory(MemoryTypes.MEMORY_SOMNIUM_NEGATIVE) / 100
				bShift = True

				for item in lPlayerState :

					sTag = item[0]
					if (sTag == "atWar") :
						if len(sText) > 0 : sText += localText.getText("[NEWLINE]", ())
						sText += localText.getText("TXT_KEY_SOMNIUM_AT_WAR", (sPlayerName, ))

					elif (sTag == "InGame") :
						if len(sText) > 0 : sText += localText.getText("[NEWLINE]", ())
						sText += localText.getText("TXT_KEY_SOMNIUM_IN_GAME", (sPlayerName, ))

					elif (sTag == "relation") :
						delay = item[1]
						if (delay > 0) :
								if len(sText) > 0 : sText += localText.getText("[NEWLINE]", ())
								sText += localText.getText("TXT_KEY_SOMNIUM_GAME_DELAYED", (sPlayerName, delay))
						else :
								if bShift :
										bShift = False
										popup.addSeparator()
								popup.addButton(localText.getText("TXT_KEY_SOMNIUM_GAME_RELATION", (sPlayerName, iPositiveChange, iNegativeChange)))
								lPlayerButtons.append((iPlayer, -1))

					elif (sTag == "gold") :
						for iGold in item[1] :
							if bShift :
								bShift = False
								popup.addSeparator()
							if iGold == 0 :
								popup.addButton(localText.getText("TXT_KEY_SOMNIUM_GAME_FUN", (sPlayerName, )))
								lPlayerButtons.append((iPlayer, iGold))
							else :
								popup.addButton(localText.getText("TXT_KEY_SOMNIUM_GAME_GOLD", (sPlayerName, iGold)))
								lPlayerButtons.append((iPlayer, iGold))

		if len(sText) > 0 :
			popup.addSeparator()
			popup.addSeparator()
			popup.setBodyString(sText)

		popup.setUserData(tuple(lPlayerButtons))
		popup.launch()

	def __EventSelectSolmniumPlayerApply(self, playerID, userData, popupReturn):
		gc = CyGlobalContext()
		game = CyGame()
		if userData :
			idButtonCliked = popupReturn.getButtonClicked()
			if idButtonCliked in xrange(len(userData)) :
				iOpponent, iGold = userData[idButtonCliked]
				gc = CyGlobalContext()
				pLeftPlayer = gc.getPlayer(playerID)
				pRightPlayer = gc.getPlayer(iOpponent)

				if not pRightPlayer.isHuman() :
					if (cs.canStartGame(playerID)) and (pLeftPlayer.isAlive()) and (pRightPlayer.isAlive()) :
						cs.startGame(playerID, iOpponent, iGold)
					else :
						CyInterface().addMessage(playerID, True, 25, CyTranslator().getText("TXT_KEY_SOMNIUM_CANT_START_GAME", (gc.getPlayer(iOpponent).getName(), )), '', 1, '', ColorTypes(7), -1, -1, False, False)
				else :
					if (cs.canStartGame(playerID)) and (cs.canStartGame(iOpponent)) and (pLeftPlayer.isAlive()) and (pRightPlayer.isAlive()) :
						if (iOpponent == game.getActivePlayer()):
							self.__EventSolmniumAcceptGameBegin((playerID, iOpponent, iGold))
					else :
						CyInterface().addMessage(playerID, True, 25, CyTranslator().getText("TXT_KEY_SOMNIUM_CANT_START_GAME", (gc.getPlayer(iOpponent).getName(), )), '', 1, '', ColorTypes(7), -1, -1, False, False)

	def __EventSolmniumAcceptGameBegin(self, argslist):
		iPlayer, iOpponent, iGold = argslist
		gc = CyGlobalContext()
		if not gc.getPlayer(iOpponent).isAlive() : return 0

		popup = PyPopup.PyPopup(CvUtil.EventSolmniumAcceptGame, EventContextTypes.EVENTCONTEXT_ALL)

		popup.setUserData(argslist)

		popup.setHeaderString(localText.getText("TXT_KEY_SOMNIUM_START", ()))
		if iGold > 0 :
			popup.setBodyString(localText.getText("TXT_KEY_SOMNIUM_ACCEPT_GAME", (gc.getPlayer(iPlayer).getName(), iGold)))
		else :
			popup.setBodyString(localText.getText("TXT_KEY_SOMNIUM_ACCEPT_GAME_FUN", (gc.getPlayer(iPlayer).getName(), )))

		popup.addButton( localText.getText("AI_DIPLO_ACCEPT_1", ()) )
		popup.addButton( localText.getText("AI_DIPLO_NO_PEACE_3", ()) )

		popup.launch(False, PopupStates.POPUPSTATE_IMMEDIATE)

	def __EventSolmniumAcceptGameApply(self, playerID, userData, popupReturn):
		gc = CyGlobalContext()
		if userData :
			iPlayer, iOpponent, iGold = userData
			idButtonCliked = popupReturn.getButtonClicked()
			if idButtonCliked == 0 :
				if (cs.canStartGame(iPlayer)) and (cs.canStartGame(iOpponent)) and (gc.getPlayer(iPlayer).isAlive()) and (gc.getPlayer(iOpponent).isAlive()) :
					cs.startGame(iPlayer, iOpponent, iGold)
				else :
					CyInterface().addMessage(iPlayer, True, 25, CyTranslator().getText("TXT_KEY_SOMNIUM_CANT_START_GAME", (gc.getPlayer(iOpponent).getName(), )), '', 1, '', ColorTypes(7), -1, -1, False, False)
					CyInterface().addMessage(iOpponent, True, 25, CyTranslator().getText("TXT_KEY_SOMNIUM_CANT_START_GAME", (gc.getPlayer(iPlayer).getName(), )), '', 1, '', ColorTypes(7), -1, -1, False, False)
			else :
				CyInterface().addMessage(iPlayer, True, 25, CyTranslator().getText("TXT_KEY_SOMNIUM_REFUSE_GAME", (gc.getPlayer(iOpponent).getName(), iGold)), '', 1, '', ColorTypes(7), -1, -1, False, False)

	def __EventSolmniumConcedeGameBegin(self, argslist):
		popup = PyPopup.PyPopup(CvUtil.EventSolmniumConcedeGame, EventContextTypes.EVENTCONTEXT_ALL)

		popup.setUserData(argslist)

		popup.setHeaderString( localText.getText("TXT_KEY_SOMNIUM_START", ()))
		popup.setBodyString( localText.getText("TXT_KEY_SOMNIUM_CONCEDE_GAME", ()))

		popup.addButton( localText.getText("AI_DIPLO_ACCEPT_1", ()) )
		popup.addButton( localText.getText("AI_DIPLO_NO_PEACE_3", ()) )

		popup.launch(False, PopupStates.POPUPSTATE_IMMEDIATE)

	def __EventSolmniumConcedeGameApply(self, playerID, userData, popupReturn):
		if userData :
			idButtonCliked = popupReturn.getButtonClicked()
			if idButtonCliked == 0 :
				cs.endGame(userData[0], userData[1])
## FfH Card Game: end
	def __eventCheatEventBegin(self, argsList):
		'Cheat Event'
		CvDebugTools.CvDebugTools().cheatEvents()
    
	def __eventCheatEventApply(self, playerID, netUserData, popupReturn):
		'Cheat Event Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyCheatEvent( (popupReturn) )

## Platy Builder ##

	def __eventWBPlayerScriptPopupApply(self, playerID, userData, popupReturn):
		sScript = popupReturn.getEditBoxString(0)
		gc.getPlayer(userData[0]).setScriptData(CvUtil.convertToStr(sScript))
		WBPlayerScreen.WBPlayerScreen().placeScript()
		return

	def __eventWBCityScriptPopupApply(self, playerID, userData, popupReturn):
		sScript = popupReturn.getEditBoxString(0)
		pCity = gc.getPlayer(userData[0]).getCity(userData[1])
		pCity.setScriptData(CvUtil.convertToStr(sScript))
		WBCityEditScreen.WBCityEditScreen(CvPlatyBuilderScreen.CvWorldBuilderScreen()).placeScript()
		return

	def __eventWBUnitScriptPopupApply(self, playerID, userData, popupReturn):
		sScript = popupReturn.getEditBoxString(0)
		pUnit = gc.getPlayer(userData[0]).getUnit(userData[1])
		pUnit.setScriptData(CvUtil.convertToStr(sScript))
		WBUnitScreen.WBUnitScreen(CvPlatyBuilderScreen.CvWorldBuilderScreen()).placeScript()
		return

	def __eventWBScriptPopupBegin(self):
		return

	def __eventWBGameScriptPopupApply(self, playerID, userData, popupReturn):
		sScript = popupReturn.getEditBoxString(0)
		CyGame().setScriptData(CvUtil.convertToStr(sScript))
		WBGameDataScreen.WBGameDataScreen(CvPlatyBuilderScreen.CvWorldBuilderScreen()).placeScript()
		return

	def __eventWBPlotScriptPopupApply(self, playerID, userData, popupReturn):
		sScript = popupReturn.getEditBoxString(0)
		pPlot = CyMap().plot(userData[0], userData[1])
		pPlot.setScriptData(CvUtil.convertToStr(sScript))
		WBPlotScreen.WBPlotScreen().placeScript()
		return

	def __eventWBLandmarkPopupApply(self, playerID, userData, popupReturn):
		sScript = popupReturn.getEditBoxString(0)
		pPlot = CyMap().plot(userData[0], userData[1])
		iPlayer = userData[2]
		if userData[3] > -1:
			pSign = CyEngine().getSignByIndex(userData[3])
			iPlayer = pSign.getPlayerType()
			CyEngine().removeSign(pPlot, iPlayer)
		if len(sScript):
			if iPlayer == gc.getBARBARIAN_PLAYER():
				CyEngine().addLandmark(pPlot, CvUtil.convertToStr(sScript))
			else:
				CyEngine().addSign(pPlot, iPlayer, CvUtil.convertToStr(sScript))
		WBPlotScreen.iCounter = 10
		return
## Platy Builder ##
