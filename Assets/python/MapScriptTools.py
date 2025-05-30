#	FILE:	   MapScriptTools.py  v1.00
#	AUTHOR:  Temudjin (2009-10)
#	PURPOSE: Provide tools to facilitate map-making and adapting existing maps.
#           Make maps compatible for 'Normal', 'Fall from Heaven 2', 'Planetfall' and 'Mars Now!' mods.
#  ====================================================================================================

#	MapScriptTools provides functions and classes to:
#  - produce maps for Planetfall or Mars Now!
#	- add Marsh terrain
#  - add Deep Ocean terrain
#  - make the map looking prettier/more realistic
#  - add special regions to the map
#  - add special features to the map
#	- replace and expand BonusBalancer (from Warlords)
#	- manipulate river creation: (starting from lakes, on islands)
#  - handle starting-positions for teams
#	- print various sorts of maps
#	- print stats about mod and map
#  - find the path for Civ4, Mod or Log files

#  -----
#	NOTES:
#  - Not really intended for 'Final Frontier' based maps.
#
#  - Compatible with BtS 3.19.
#    I've run a short test with Warlords 2.13 and that worked fine too.
#    The above statement seems to imply compatibility to BtS 3.13/3.17, but this isn't tested.
#
#    Actually the question of compatibility arises mostly with respect of
#    recognizing and showing the right mod-versions.
#    Unless recognition of 'Planetfall', 'Mars Now!' and 'Fall from Heaven 2' fails,
#    there shouldn't be any problems beyond logging false identifications.
#
#  - Multiplayer compatibility is unknown.
#    (Seems probable though as all randomizations are centralized within the choose..() functions.)
#    Please tell me.
#
#  - MAC compatibility is unknown but improbable.
#    (I think they use Python 2.3 and sets are not known. I believe I used them only twice though.
#    Feel free to adjust the file yourself as I do not own a MAC)
#    Please tell me.
#  -----

#  =====================
#  Temudjin 15.July.2010
#  =====================

#	Changelog
#	---------
#	1.00					initial release
#
from CvPythonExtensions import *
import CvMapGeneratorUtil
import CvUtil
import inspect
import os
import os.path
import sys


#################################################
### Defined Class Instances
#################################################
### randomList = RandomList()
### civFolders = CivFolders()
### deepOcean = DeepOcean()
### planetFallMap = PlanetFallMap()
### mapPrettifier = MapPrettifier()
### marshMaker = MarshMaker()
### mapRegions = MapRegions()
### featurePlacer = FeaturePlacer()
### bonusBalancer = BonusBalancer()
### riverMaker = RiverMaker()
### teamStart = TeamStart()
### mapPrint = MapPrint()
### mapStats = MapStats()
#################################################

DEBUG = False

def getVersion():
	return "1.00"
def getDescription():
	return "MapScriptTools:\n Tools to facilitate map making.\n This is not a map-script!"

####################################################################################################
########## Set ModInfo Global Variables - should be called: first thing in beforeGeneration()
####################################################################################################
# get infos about the mod, print infos
def getModInfo( mapVersion=None, defLatitude=None, sMapInfo=None ):
	print "[MST] ===== getModInfo()"

	if DEBUG:
		global callModule
		stackList = inspect.stack()
		printList( stackList, "stack:", 1, prefix="[MST] " )
		callModule = ""
		if len( stackList ) > 1:
			callModule = stackList[1][1]
		print "[MST] callModule: %s" % ( callModule )

	########################
	### initialization check
	########################
	global bInitialized
	try:
		test = bInitialized
		bInitialized = True
	except:
		bInitialized = False

	###########################
	### civ universal constants
	###########################
	global gc, map, game, dice
	global iNumPlotsX, iNumPlotsY
	gc   		  = CyGlobalContext()
	map  		  = CyMap()
	game 		  = CyGame()
	dice 		  = gc.getGame().getMapRand()
	iNumPlotsX = map.getGridWidth()
	iNumPlotsY = map.getGridHeight()

	##############################
	### define cardinal directions
	##############################
	global ecNone, ecNorth, ecEast, ecSouth, ecWest

	ecNone  = CardinalDirectionTypes.NO_CARDINALDIRECTION
	ecNorth = CardinalDirectionTypes.CARDINALDIRECTION_NORTH
	ecEast  = CardinalDirectionTypes.CARDINALDIRECTION_EAST
	ecSouth = CardinalDirectionTypes.CARDINALDIRECTION_SOUTH
	ecWest  = CardinalDirectionTypes.CARDINALDIRECTION_WEST

	#######################
	### retrieve parameters
	#######################
	global mapGetLatitude

	# defLatitude should evaluate to a value between 0 .. 90, using y and/or x
	sMapName = map.getMapScriptName()
	if not mapVersion==None:
		sMapName += " " + mapVersion
	if defLatitude==None:
		mapGetLatitude = "noPolesGetLatitude(x,y)"		# default - gives value between 0..90
	else:
		mapGetLatitude = defLatitude							# shoud give value between 0..90 but negative is ok
	# adjust sMapInfo for Python Error with percent chars
	if sMapInfo == None:
		mapInfo = ""
	else:
		mapInfo = str( sMapInfo )
		mapInfo = mapInfo.replace( "%", "%%" )

	################
	### get mod name
	################
	modName = ""
	if bInitialized:
		civFolders.getModPaths()
		modName   = civFolders.modName
		modFolder = civFolders.modFolder
		modDir    = civFolders.modDir

	###########################
	### recongnize civ versions
	###########################
	global bBTS, bWarlords, bVanilla

	sVersion = unicode(CyTranslator().getText("TXT_KEY_BTS_CIVS", ()))					# check for BtS
#	print "[MST] " + sVersion
	bBTS = (sVersion.find("Beyond the Sword") > -1)

	sVersion = unicode(CyTranslator().getText("TXT_KEY_MAIN_MENU_WARLORS", ()))		# check for Warlords
#	print "[MST] " + sVersion
	bWarlords = (not bBTS) and (sVersion.find("Warlords") > -1)

	sVersion = unicode(CyTranslator().getText("TXT_KEY_MAIN_MENU_ABOUT_CIV4", ()))	# check for Vanilla
#	print "[MST] " + sVersion
	bVanilla = (not bBTS) and (not bWarlords) and (sVersion.find("Civ 4") > -1)

	#########################
	### recongnize super mods
	#########################
	global bPatch, bAIAuto, bBBAI, bBUG

	bPatch = checkPatch()												# Unofficial patch
	bAIAuto = checkAIAuto()												# AI AutoPlay
	bBBAI = checkBBAI()													# Better BtS AI
	bBUG = checkBUG()														# BtS Unaltered Gameplay

	# get BUG-ModName and BUG-ModVersion if possible
	if bBUG:
		bugModName = None
		try:
			import CvModName as BUGname
			bugModName = BUGname.modName
			bugModVersion = BUGname.modVersion
			if bugModName.find( bugModVersion ) == -1:
				bugModName += " " + bugModVersion
			sprint  = "[MST] bugModName: %r\n" % bugModName
			sprint +="[MST] bugModVersion: %r" % bugModVersion
			print sprint

		except:
			pass

	########################
	### recognize base mods
	########################
	global bFFH, bPfall, bMars, bFFront

	bPfall = isBonus( "Fungicide" )													# Fungicide means 'Planetfall'
	bFFH = isBonus( "Mana" )															# Mana means 'Fall from Heaven'
	bFFront = gc.getInfoTypeForString('FEATURE_SOLAR_SYSTEM') > -1			# SolarSystem means 'Final Frontier'

	sTxt = unicode(CyTranslator().getText("TXT_KEY_PEDIA_CATEGORY_CONCEPT_NEW", ()))		# 'Mars Now!'
	bMars = (sTxt.find("Mars, Now!") > 1) or (sTxt.find("Mars, Jetzt!") > 1)				# 'Mars Now!'

	#############################
	### recongnize different mods
	#############################
	global bFF, bFFlat, bOrbis, bRoD, bLE, bWMana, bRifE
	global bTrek, bMOO
	global bLoR, bRoM, bTW, bHoTK, bHitM, bOver, bQC

	# FFH - Fall Further
	sVersion = unicode(CyTranslator().getText("TXT_KEY_VERSION", ()))		# Fall Further does it right !
	bFF = (sVersion.find("Fall Further") > -1)									# we can even get the patch version
	if bFF:
		n1 = sVersion.find( '(' )
		n2 = sVersion.find( ')' )
		modName = " Fall Further " + sVersion[n1+1:n2]

	# FFH - Fall Flat
	sVersion = unicode(CyTranslator().getText("TXT_KEY_VERSION", ()))		# Fall Flat does it right !
	bFFlat = (sVersion.find("Fall Flat") > -1)

	# FFH - Orbis
	sVersion = unicode(CyTranslator().getText("TXT_KEY_VERSION", ()))		# Orbis does it right !
	bOrbis = (sVersion.find("Orbis") > -1)

	# FFH - Rise of Darkness
	bRoD   = ( modName.lower().find( "rise of darkness") >-1 ) and bFFH	# 'Rise of Darkness' Mod

	# FFH - Leaders Enhanced
	sVersion = unicode(CyTranslator().getText("TXT_KEY_VERSION", ()))		# Leaders Enhanced does it right !
	bLE = (sVersion.find("LeadersEnhanced") > -1)

	# FFH - Wildmana
	bWMana = ( modName.lower().find( "wild mana")>-1 ) and bFFH				# 'WildMana' Mod

	# FFH - Rise from Erebus
	sVersion = unicode(CyTranslator().getText("TXT_KEY_VERSION", ()))		# Rise from Erebus does it right !
	bRifE = (sVersion.find("Ashes of Erebus") > -1)

	# FinalFrontier - Star Trek
	bTrek  = ( gc.getInfoTypeForString('ERA_TOS') > -1 )						# 'Tos' means Star Trek

	# FinalFrontier - Master of Orion
	bMOO   = ( gc.getInfoTypeForString('CIVILIZATION_SAKKRA') > -1 )		# 'Sakkra' means Master of Orion

	# Legends Of Revolution
	sVersion = unicode(CyTranslator().getText("TXT_KEY_CONCEPT_LOR_REVOLUTIONS_PEDIA", ()))
	bLoR = (sVersion.find("Legends of Revolution") > -1)

	# Rise of Mankind
	sVersion = unicode(CyTranslator().getText("TXT_KEY_CONCEPT_ROM_RELIGION_PEDIA", ()))
	bRoM = (sVersion.find("Rise of Mankind") > -1)

	# Thomas' War
	sVersion = unicode(CyTranslator().getText("TXT_KEY_NEW_CIV", ()))
	bTW = (sVersion.find("Thomas' War") > -1)

	# The History of Three Kingdoms
	sVersion = unicode(CyTranslator().getText("TXT_KEY_BUG_CREATED_BY_HEADER", ()))
	bHoTK = (sVersion.find("History of Three Kingdoms") > -1)

	# History in the Making
	sVersion = unicode(CyTranslator().getText("TXT_KEY_DCM_TEXT", ()))
	bHitM = (sVersion.find("History in the Making") > -1)

	# Overlord
	sVersion = unicode(CyTranslator().getText("TXT_KEY_GAMESPEED_FXOVERLORD", ()))
	bOver = (sVersion.find("OverLord") > -1)

	# Quot Capita
	bQC = ( modName.lower().find( "quot capita")>-1 )

	###############################
	### define globals for terrains
	###############################
	global etOcean, etCoast, etGrass, etPlains, etDesert, etTaiga, etTundra
	global etTrench, etShelf, etFlatRainy, etRockyRainy
	global etFlatMoist, etRockyMoist, etFlatArid, etRockyArid, etFlatPolar, etRockyPolar
	global etBurningSands, etBrokenLands, etFieldsOfPerdition, etShallows
	global etMarsh, etBlightedCoast, etBlackwater
	global bMarsh, bBlightedCoast, bBlackwater
	global etOceanDeep, bOceanDeep

	# define known terrains
	bMarsh  = False
	etOcean     = gc.getInfoTypeForString('TERRAIN_OCEAN')
	etCoast     = gc.getInfoTypeForString('TERRAIN_COAST')
	etOceanDeep = gc.getInfoTypeForString('TERRAIN_OCEAN_DEEP')
	bOceanDeep  = ( etOceanDeep >= 0 )
	if etOceanDeep == -1: etOceanDeep = etOcean
	if bPfall:
		etFlatRainy		= gc.getInfoTypeForString('TERRAIN_FLAT_RAINY')		# Marsh, Grass
		etRockyRainy	= gc.getInfoTypeForString('TERRAIN_ROCKY_RAINY')	# Grass
		etFlatMoist		= gc.getInfoTypeForString('TERRAIN_FLAT_MOIST')		# Plains 1
		etRockyMoist	= gc.getInfoTypeForString('TERRAIN_ROCKY_MOIST')	# Plains 2, Taiga
		etFlatArid		= gc.getInfoTypeForString('TERRAIN_FLAT_ARID')		# Desert 1
		etRockyArid		= gc.getInfoTypeForString('TERRAIN_ROCKY_ARID')		# Desert 2
		etFlatPolar		= gc.getInfoTypeForString('TERRAIN_FLAT_POLAR')		# Taiga, Tundra
		etRockyPolar	= gc.getInfoTypeForString('TERRAIN_ROCKY_POLAR')	# Tundra
		etShelf			= gc.getInfoTypeForString('TERRAIN_SHELF')
		etTrench			= gc.getInfoTypeForString('TERRAIN_TRENCH')
	else:
		etDesert			= gc.getInfoTypeForString('TERRAIN_DESERT')			# FlatArid, RockyArid
		etPlains			= gc.getInfoTypeForString('TERRAIN_PLAINS')			# FlatMoist, RockyMoist
		etGrass 			= gc.getInfoTypeForString('TERRAIN_GRASS')			# FlatRainy, RockyRainy
		etTaiga			= gc.getInfoTypeForString('TERRAIN_TAIGA')			# RockyMoist, FlatPolar
		etTundra			= gc.getInfoTypeForString('TERRAIN_TUNDRA')				# FlatPolar, RockyPolar
		etMarsh 			= gc.getInfoTypeForString("TERRAIN_MARSH")			# FlatRainy
		if etMarsh<0: etMarsh = etGrass
		bMarsh = ( etMarsh != etGrass )
		if bFFH:
			etBurningSands		  = gc.getInfoTypeForString('TERRAIN_BURNING_SANDS')			# Hell-Terrain Desert
			etBrokenLands		  = gc.getInfoTypeForString('TERRAIN_BROKEN_LANDS')				# Hell-Terrain Grass
			etFieldsOfPerdition = gc.getInfoTypeForString('TERRAIN_FIELDS_OF_PERDITION')		# Hell-Terrain Plains
			etShallows			  = gc.getInfoTypeForString('TERRAIN_SHALLOWS')					# Hell-Terrain Marsh
	# known other terrains, which may exist - or not
	etBlightedCoast = gc.getInfoTypeForString('TERRAIN_BLIGHTED_COAST')		# Hell-Terrain Coast
	bBlightedCoast  = ( etBlightedCoast >= 0 )
	etBlackwater	 = gc.getInfoTypeForString('TERRAIN_BLACKWATER')		# Hell-Terrain Ocean
	bBlackwater     = ( etBlackwater >= 0 )

	###############################
	### define globals for features
	###############################
	global efIce, efFallout, efForest, efJungle, efOasis, efFloodPlains
	global efTrench, efSeaFungus, efXenoFungus, efHybridForest, efRadiation
	global efForestBurnt, efForestNew, efForestAncient, efFlames, efTormentedSouls
	global efSwamp, efStorm, efKelp, efVolcano, efVolcanoDormant, efScrub, efCrystalPlains
	global efHauntedLands, efBlizzard, efObsidianPlains
	global bSwamp, bStorm, bKelp, bVolcano, bVolcanoDormant, bScrub, bCrystalPlains
	global bHauntedLands, bBlizzard, bObsidianPlains

	# define known features
	efIce         = gc.getInfoTypeForString('FEATURE_ICE')
	efFallout     = gc.getInfoTypeForString('FEATURE_FALLOUT')
	efForest      = gc.getInfoTypeForString('FEATURE_FOREST')
	efJungle      = gc.getInfoTypeForString('FEATURE_JUNGLE')
	if bPfall:
		efTrench       = gc.getInfoTypeForString('FEATURE_TRENCH')
		efSeaFungus    = gc.getInfoTypeForString('FEATURE_SEA_FUNGUS')
		efXenoFungus   = gc.getInfoTypeForString('FEATURE_XENOFUNGUS')
		efHybridForest = gc.getInfoTypeForString('FEATURE_HYBRID_FOREST')
		efRadiation    = gc.getInfoTypeForString('FEATURE_RADIATION')
	else:
		efOasis       = gc.getInfoTypeForString('FEATURE_OASIS')
		efFloodPlains = gc.getInfoTypeForString('FEATURE_FLOOD_PLAINS')
		if bFFH:
			efForestBurnt    = gc.getInfoTypeForString('FEATURE_FOREST_BURNT')
			efForestNew      = gc.getInfoTypeForString('FEATURE_FOREST_NEW')
			efForestAncient  = gc.getInfoTypeForString('FEATURE_FOREST_ANCIENT')
			efFlames         = gc.getInfoTypeForString('FEATURE_FLAMES')
			efTormentedSouls = gc.getInfoTypeForString('FEATURE_TORMENTED_SOULS')
			# plus walls and doors - are they used?

	# known other features, which may exist - or not
	efSwamp          = gc.getInfoTypeForString('FEATURE_SWAMP')					#
	bSwamp           = ( efSwamp >= 0 )
	efStorm          = gc.getInfoTypeForString('FEATURE_STORM')					#
	bStorm           = ( efStorm >= 0 )
	efKelp           = gc.getInfoTypeForString('FEATURE_KELP')					# terain_coast
	bKelp            = ( efKelp >= 0 )
	efVolcano        = gc.getInfoTypeForString('FEATURE_VOLCANO')				# plot_peak
	bVolcano         = ( efVolcano >= 0 )
	efVolcanoDormant = gc.getInfoTypeForString('FEATURE_VOLCANO_DORMANT')		# plot_peak
	bVolcanoDormant  = ( efVolcanoDormant >= 0 )
	efScrub          = gc.getInfoTypeForString('FEATURE_SCRUB')					# terrain_desert
	bScrub           = ( efScrub >= 0 )
	efBlizzard       = gc.getInfoTypeForString('FEATURE_BLIZZARD')				# terrain_snow, terrain_tundra
	bBlizzard        = ( efBlizzard >= 0 )
	efCrystalPlains  = gc.getInfoTypeForString('FEATURE_CRYSTAL_PLAINS')		# terrain_snow, riverside & flat
	bCrystalPlains   = ( efCrystalPlains >= 0 )
	efHauntedLands   = gc.getInfoTypeForString('PLOT_EFFECT_HAUNTED_LANDS')			# plot_land, plot_hill
	bHauntedLands    = ( efHauntedLands >= 0 )
	efObsidianPlains = gc.getInfoTypeForString('FEATURE_OBSIDIAN_PLAINS')		# terrain_burning_sands / terrain_marsh
	bObsidianPlains  = ( efObsidianPlains >= 0 )

	################################
	### define globals for some boni
	################################
	global ebAluminum, ebBauxite, ebCopper, ebHorse, ebIron, ebMithril, ebNaturalGas
	global ebOil, ebReagens, ebRubber, ebSulphur, ebTitanium, ebUranium
	global ebMana, ebManaEarth, ebManaWater, ebManaAir, ebManaFire, ebManaChaos, ebManaEntropy
	global ebManaDeath, ebManaShadow, ebManaSun, ebManaSpirit, ebManaMind, ebManaLaw
	global ebManaNature, ebManaLife, ebManaBody, ebManaEnchantment, ebManaMetamagic
	global ebManaDimensional, ebManaCreation, ebManaForce, ebManaIce, ebManaRefined
	global ebCoal, ebClam, ebFish, ebCrab, ebShrimp, ebGold, ebSilver, ebBanana
	global ebCow, ebDeer, ebFur, ebGems, ebMarble, ebSheep
	global ebFungicide, ebFungalGin, ebGrenadeFruits, ebPholusMutagen, ebRareDnaMoist, ebRareDnaOcean
	global ebRareDnaRainy, ebRareDnaTropical, ebBoreHoleCluster, ebResonanceCluster, ebArtifact
	global ebDimensionalGate, ebManifoldNexus, ebMonolith, ebTheRuins, ebThorium, ebIridium
	global ebAlgaeCyan, ebMineral, ebEnergy

	# strategic boni
	ebAluminum        = gc.getInfoTypeForString('BONUS_ALUMINUM')				#
	ebBauxite         = gc.getInfoTypeForString('BONUS_BAUXITE')				#
	ebCopper          = gc.getInfoTypeForString('BONUS_COPPER')					#
	ebHorse           = gc.getInfoTypeForString('BONUS_HORSE')					#
	ebIron            = gc.getInfoTypeForString('BONUS_IRON')					#
	ebMithril         = gc.getInfoTypeForString('BONUS_MITHRIL')				# FFH:
	ebNaturalGas      = gc.getInfoTypeForString('BONUS_NATURAL_GAS')			#
	ebOil             = gc.getInfoTypeForString('BONUS_OIL')					# not plains, Pfall: water
	ebReagens         = gc.getInfoTypeForString('BONUS_REAGENTS')				# FFH:
	ebRubber          = gc.getInfoTypeForString('BONUS_RUBBER')					#
	ebSulphur         = gc.getInfoTypeForString('BONUS_SULPHUR')				#
	ebTitanium        = gc.getInfoTypeForString('BONUS_TITANIUM')				#
	ebUranium         = gc.getInfoTypeForString('BONUS_URANIUM')				#

	# mana boni
	ebMana            = gc.getInfoTypeForString('BONUS_MANA')					# FFH:
	ebManaEarth       = gc.getInfoTypeForString('BONUS_MANA_EARTH')			# FFH:
	ebManaWater       = gc.getInfoTypeForString('BONUS_MANA_WATER')			# FFH:
	ebManaAir         = gc.getInfoTypeForString('BONUS_MANA_AIR')				# FFH:
	ebManaFire        = gc.getInfoTypeForString('BONUS_MANA_FIRE')				# FFH:
	ebManaChaos       = gc.getInfoTypeForString('BONUS_MANA_CHAOS')			# FFH:
	ebManaEntropy     = gc.getInfoTypeForString('BONUS_MANA_ENTROPY')			# FFH:
	ebManaDeath       = gc.getInfoTypeForString('BONUS_MANA_DEATH')			# FFH:
	ebManaShadow      = gc.getInfoTypeForString('BONUS_MANA_SHADOW')			# FFH:
	ebManaSun         = gc.getInfoTypeForString('BONUS_MANA_SUN')				# FFH:
	ebManaSpirit      = gc.getInfoTypeForString('BONUS_MANA_SPIRIT')			# FFH:
	ebManaMind        = gc.getInfoTypeForString('BONUS_MANA_MIND')				# FFH:
	ebManaLaw         = gc.getInfoTypeForString('BONUS_MANA_LAW')				# FFH:
	ebManaNature      = gc.getInfoTypeForString('BONUS_MANA_NATURE')			# FFH:
	ebManaLife        = gc.getInfoTypeForString('BONUS_MANA_LIFE')				# FFH:
	ebManaBody        = gc.getInfoTypeForString('BONUS_MANA_BODY')				# FFH:
	ebManaEnchantment = gc.getInfoTypeForString('BONUS_MANA_ENCHANTMENT')	# FFH:
	ebManaMetamagic   = gc.getInfoTypeForString('BONUS_MANA_METAMAGIC')		# FFH:
	ebManaIce         = gc.getInfoTypeForString('BONUS_MANA_ICE')				# FFH:
	ebManaDimensional = gc.getInfoTypeForString('BONUS_MANA_DIMENSIONAL')	# FFH:
	ebManaCreation    = gc.getInfoTypeForString('BONUS_MANA_CREATION')		# FFH:
	ebManaForce       = gc.getInfoTypeForString('BONUS_MANA_FORCE')			# FFH:
	ebManaRefined     = gc.getInfoTypeForString('BONUS_REFINED_MANA')			# FFH: Orbis

	# define other known boni
	ebClam            = gc.getInfoTypeForString('BONUS_CLAM')					# water
	ebCrab            = gc.getInfoTypeForString('BONUS_CRAB')					# water
	ebFish            = gc.getInfoTypeForString('BONUS_FISH')					# water
	ebShrimp          = gc.getInfoTypeForString('BONUS_SHRIMP')					# water
	ebCoal            = gc.getInfoTypeForString('BONUS_COAL')					#
	ebGold            = gc.getInfoTypeForString('BONUS_GOLD')					# plains, desert, Pfall: any
	ebSilver          = gc.getInfoTypeForString('BONUS_SILVER')					# taiga or tundra, Pfall: any
	ebBanana          = gc.getInfoTypeForString('BONUS_BANANA')					# grass & jungle
	ebCow             = gc.getInfoTypeForString('BONUS_COW')						# grass, plains
	ebDeer            = gc.getInfoTypeForString('BONUS_DEER')					# tundra & forest
	ebFur             = gc.getInfoTypeForString('BONUS_FUR')						# taiga or tundra, forest
	ebGems            = gc.getInfoTypeForString('BONUS_GEMS')					# grass, jungle
	ebMarble          = gc.getInfoTypeForString('BONUS_MARBLE')					# plains, taiga or tundra
	ebSheep           = gc.getInfoTypeForString('BONUS_SHEEP')					# grass or plains

	ebFungicide        = gc.getInfoTypeForString('BONUS_FUNGICIDE')			# Pfall: non polar
	ebFungalGin        = gc.getInfoTypeForString('BONUS_FUNGAL_GIN')			# Pfall:
	ebGrenadeFruits    = gc.getInfoTypeForString('BONUS_GRENADE_FRUITS')		# Pfall: flat, not polar
	ebPholusMutagen    = gc.getInfoTypeForString('BONUS_PHOLUS_MUTAGEN')		# Pfall:
	ebRareDnaMoist     = gc.getInfoTypeForString('BONUS_RARE_DNA_MOIST')		# Pfall: moist
	ebRareDnaOcean     = gc.getInfoTypeForString('BONUS_RARE_DNA_OCEAN')		# Pfall: ocean
	ebRareDnaRainy     = gc.getInfoTypeForString('BONUS_RARE_DNA_RAINY')		# Pfall: rainy
	ebRareDnaTropical  = gc.getInfoTypeForString('BONUS_RARE_DNA_TROPICAL')	# Pfall: rainy
	ebBoreHoleCluster  = gc.getInfoTypeForString('BONUS_BOREHOLE_CLUSTER')	# Pfall:
	ebResonanceCluster = gc.getInfoTypeForString('BONUS_RESONANCE_CLUSTER')	# Pfall:
	ebArtifact         = gc.getInfoTypeForString('BONUS_ARTIFACT')				# Pfall:
	ebDimensionalGate  = gc.getInfoTypeForString('BONUS_DIMENSIONAL_GATE')	# Pfall:
	ebManifoldNexus    = gc.getInfoTypeForString('BONUS_MANIFOLD_NEXUS')		# Pfall:
	ebMonolith         = gc.getInfoTypeForString('BONUS_MONOLITH')				# Pfall:
	ebTheRuins         = gc.getInfoTypeForString('BONUS_THE_RUINS')			# Pfall:
	ebThorium          = gc.getInfoTypeForString('BONUS_THORIUM')				# Pfall:
	ebIridium          = gc.getInfoTypeForString('BONUS_IRIDIUM')				# Pfall:
	ebAlgaeCyan        = gc.getInfoTypeForString('BONUS_ALGAE_CYAN')			# Pfall:
	ebEnergy           = gc.getInfoTypeForString('BONUS_ENERGY')				# Pfall:
	ebMineral          = gc.getInfoTypeForString('BONUS_MINERAL')				# Pfall:

	###################################
	### define globals for improvements
	###################################
	global eiCityRuins, eiGoody
	global eiFarm, eiMine, eiWindmill
	global eiTrench, eiGreenhouse, eiSolarCollector									# Planetfall

	# define known improvements
	eiCityRuins = gc.getInfoTypeForString('IMPROVEMENT_CITY_RUINS')			# plot_land, plot_hill
	eiGoody = gc.getInfoTypeForString( 'IMPROVEMENT_GOODY_HUT' )
	eiFarm = gc.getInfoTypeForString( 'IMPROVEMENT_FARM' )
	eiMine = gc.getInfoTypeForString( 'IMPROVEMENT_MINE' )
	if eiMine < 0:
		eiMine = gc.getInfoTypeForString( 'IMPROVEMENT_MINE2' )
	eiWindmill = gc.getInfoTypeForString( 'IMPROVEMENT_WINDMILL' )

	if bPfall:
		eiTrench = gc.getInfoTypeForString('IMPROVEMENT_TRENCH')
		eiGreenhouse = gc.getInfoTypeForString( 'IMPROVEMENT_GREENHOUSE' )
		eiSolarCollector = gc.getInfoTypeForString( 'IMPROVEMENT_SOLAR_COLLECTOR' )

	##############################
	### Not available at init time
	##############################
	global sClimateType, sSeaType, sWorldType, sEraType
	global iPlayers, bTeams

	sprint = ""
	if not bInitialized:
		civ = ' Civ 4 - ' + iif( bBTS, 'Beyond the Sword', iif( bVanilla, '(Vanilla)', 'Warlords' ) )
		iName = len(civ) + 1
		sprint += "[MST]   " + "-" * iName + "\n"
		sprint += "[MST]   " + civ + "\n"
		sprint += "[MST]   " + "-" * iName + "\n"
		sprint += "\n"
		sprint += "[MST]   Mod Capabilities for Maps:\n"
		sprint += "[MST]   --------------------------\n"
		print sprint
		mapStats.mapStatistics( False )
	else:
		print
		sprint += "[MST] " + "################################################################### MapScriptTools:getModInfo() ### \n"
		sprint += "[MST] " + "Initialization Parameters: - %s, - %s \n\n" % (sMapName, mapGetLatitude)

		###############################
		### user selected map constants
		###############################
		# MapType
		sClimateType = gc.getClimateInfo(map.getClimate()).getType()
		sSeaType     = gc.getSeaLevelInfo(map.getSeaLevel()).getType()
		sWorldType   = gc.getWorldInfo(map.getWorldSize()).getType()
		sEraType     = gc.getEraInfo(game.getStartEra()).getType()
		# Difficulty
		sDifficulty = gc.getHandicapInfo(gc.getGame().getHandicapType()).getType()
		# GameSpeed
		sGameSpeed = gc.getGameSpeedInfo(gc.getGame().getGameSpeedType()).getType()
		iGameTurns = game.getMaxTurns()
		iGameYears = gc.getGame().getTurnYear(iGameTurns) - gc.getGame().getTurnYear(0)
		# PlayerNumber, HasTeams
		iPlayers = gc.getGame().countCivPlayersEverAlive()				# number of players
		bTeams = teamStart.getTeams()											# check if there are teams

		########################
		### print map & mod info
		########################
		iName = max( len(modName), len(sMapName) - 5 )
		sprint += "[MST] " + "==============================%s \n" % ( '='*iName )
		sprint += "[MST] " + "Map Script Features      Mod: %s \n" % ( capWords( modName ) )
		sprint += "[MST] " + "----------------------   -----%s \n" % ( '-'*iName )
		sprint += "[MST] " + "MapScriptName:           %s \n\n" % ( sMapName )
		sprint += "[MST] " + "Players/MaxPlayers:      %i / %i \n" % ( iPlayers, gc.getMAX_PLAYERS()-1 )
		sprint += "[MST] " + "Difficulty Level:        %s \n" % ( sDifficulty[9:].capitalize() )
		if bTeams:
			sprint += "[MST] " + "- Teams:                 %r \n" % ( teamStart.teamDict )
			humDict = {}
			for k in teamStart.humanDict: humDict[k] = iif(teamStart.humanDict[k]==2,'True',iif(teamStart.humanDict[k]==1,'Some','False'))
			sprint += "[MST] " + "- Team-Humanity:         %r \n" % ( humDict )
		sprint += "[MST] " + "WorldArea: Size          %i x %i \n"  % ( iNumPlotsX, iNumPlotsY )
		sprint += "[MST] " + "Mapsize:                 %s Map - %i Plots \n" % ( sWorldType[10:].capitalize(), map.numPlots() )
		sprint += "[MST] " + "GameSpeed:               %s Speed - %i Turns, %i Years \n" % ( sGameSpeed[10:].capitalize(), iGameTurns, iGameYears )
		sprint += "[MST] " + "Era:                     %s Era \n" % ( sEraType[4:].capitalize() )
		if bFFront:
			sprint += "\n"
		else:
			sprint += "[MST] " + "Climate, Sealevel:       %s, %s Seas \n" % ( sClimateType[8:].capitalize(), sSeaType[9:].capitalize() )
			neg = ( evalLatitude(map.plot(iNumPlotsX-1,iNumPlotsY-1)) > evalLatitude(map.plot(iNumPlotsX-2,iNumPlotsY-2)) )
			sprint += "[MST] " + "Latitude: Max,Min        %i, %s%i \n" % ( evalLatitude( map.plot(0,0) ), iif(neg,"-",""), evalLatitude( map.plot(iNumPlotsX-1,iNumPlotsY-1) ) )
		if sMapInfo != None:
			sprint += "[MST] " + "----------------------   -----%s \n" % ( '-'*iName )
			sprint += mapInfo
			sprint += "[MST] " + "----------------------   -----%s \n" % ( '-'*iName )
		sprint += "[MST] " + "Deep Ocean:              %r \n" % ( bOceanDeep )
		sprint += "[MST] " + "Marsh, Volcano:          %r, %r \n" % ( bMarsh, bVolcano )
		sprint += "[MST] " + "Kelp, Scrub:             %r, %r \n" % ( bKelp, bScrub )
		if bFFH:
			sprint += "[MST] " + "Haunted Lands            %r \n" % ( bHauntedLands )
			sprint += "[MST] " + "Crystal Plains           %r \n" % ( bCrystalPlains )
		sprint += "\n"

		sprint += "[MST] " + "Mod-DLL is patched:      %r\n" % ( bPatch )
		sprint += "[MST] " + "Uses AI AutoPlay:        %r\n" % ( bAIAuto )
		sprint += "[MST] " + "Uses Better BtS AI:      %r\n" % ( bBBAI )
		sprint += "[MST] " + "Uses BUG:                %r\n" % ( bBUG )
		sprint += "[MST] " + "----------------------   -----%s \n" % ( '-'*iName )
		sprint += "[MST] " + "Planetfall:              %r\n" % ( bPfall )
		sprint += "[MST] " + "Mars Now!:               %r\n" % ( bMars )
		if not bFFront:
			sprint += "[MST] " + "Final Frontier:          %r\n" % ( bFFront )
		else:
			sprint += "[MST] " + "Final Frontier:          %r\n" % ( bFFront )
			if bTrek:
				sprint += "[MST] " + "  - Star Trek:           %r\n" % (bTrek)
			elif bMOO:
				sprint += "[MST] " + "  - MOO2Civ:             %r\n" % (bMOO)
		if not bFFH:
			sprint += "[MST] " + "Fall From Heaven:        %r\n" % ( bFFH )
		else:
			sprint += "[MST] " + "Fall From Heaven:        %r\n" % ( bFFH )
			if bFF or bFFlat:
				sprint += "[MST] " + "- Fall Further:          %r\n" % (bFF)
			if bFFlat:
				sprint += "[MST] " + "  - Fall Flat:           %r\n" % (bFFlat)
			if bOrbis or bLE:
				sprint += "[MST] " + "- Orbis:                 %r\n" % (bOrbis)
			if bLE:
				sprint += "[MST] " + "  - Leaders Enhanced:    %r\n" % (bLE)
			if bRoD:
				sprint += "[MST] " + "- Rise of Darkness:      %r\n" % (bRoD)
			if bWMana:
				sprint += "[MST] " + "- Wild Mana:             %r\n" % (bWMana)
			if bRifE:
				sprint += "[MST] " + "- Ashes of Erebus:      %r\n" % (bRifE)
		if bBUG and	(bugModName != None):
			sprint += "\n"
			sprint += "[MST] " + "%s \n" % ( capWords( bugModName ) )
		else:
			if bLoR:
				sprint += "\n"
				sprint += "[MST] " + "Legends of Revolution \n"
			elif bTW:
				sprint += "\n"
				sprint += "[MST] " + "Thomas' War \n"
			elif bHoTK:
				sprint += "\n"
				sprint += "[MST] " + "History of Three Kingdoms \n"
			elif bRoM:
				sprint += "\n"
				sprint += "[MST] " + "Rise of Mankind \n"
			elif bHitM:
				sprint += "\n"
				sprint += "[MST] " + "History in the Making \n"
			elif bQC:
				sprint += "\n"
				sprint += "[MST] " + "Quot Capita \n"
			elif bOver:
				sprint += "\n"
				sprint += "[MST] " + "Overlord \n"

		sprint += "[MST] " + "==============================%s \n" % ( '='*iName )
		print sprint
		print "[MST] " + "################################################################### MapScriptTools:getModInfo() ###"

		#####################################
		### initialize classes (where needed)
		#####################################
		marshMaker.initialize()
		mapRegions.initialize()
		mapPrint.initialize()

		# debug maps; check if given defLatitude parameter is reasonable
		if DEBUG: testLatitude()


#######################################################################
########## ModInfo Functions
#######################################################################
# latitude = evalLatitude( y, bDegrees=True )
# iLat = noPolesGetLatitude( x, y )
# iLat = dllGetLatitude( x, y )
# iLat = floatGetLatitude( x, y )
# bPatch = checkPatch()
# bAIAuto = checkAIAuto()
# bBBAI = checkBBAI()
# bBUG = checkBUG()
# testLatitude()
# bool = isCivilization( sInfo )
# bool = isBonus( sInfo )
# bool = isLeaderHead( sInfo )
#######################################################################

# evaluate code given to ModInfo, to find latitude for plot
# - use noPolesGetLatitude() if evaluation fails
# - mapGetLatitude should evaluate to a value between 0 .. 90, using y and/or x
def evalLatitude( plot, bDegrees=True ):
	if plot.isNone():
		stackList = inspect.stack()
		printList( stackList, "stack:", 1, prefix="[MST] " )
		print "ERROR!: evalLatitude() failed! Bad plot!"
		return 0

	x = plot.getX()
	y = plot.getY()
	try:
		iLat = abs( eval( mapGetLatitude ) )		# should give value between 0..90
		if iLat > 90:
			iLat = noPolesGetLatitude(x,y)
			fLat = iLat / 90.0
			print "WARNING!: evalLatitude() outside range! Latitude(%3i,%2i) = %2i, %6.3f - '%s'" % (x,y,iLat,fLat,mapGetLatitude)
			return iif( bDegrees, iLat, fLat )
	except:
		iLat = noPolesGetLatitude(x,y)
		fLat = iLat / 90.0
		print "WARNING!: evalLatitude() failed! Latitude(%3i,%2i) = %2i, %6.3f - '%s'" % (x,y,iLat,fLat,mapGetLatitude)
		return iif( bDegrees, iLat, fLat )

	fLat = iLat / 90.0
	iLat = int( round( iLat ) )
	return iif( bDegrees, iLat, fLat )

# get latitude 0..90 for given x,y coordinates
# - uses floating-point for precision
#   eually distributed, does not include poles or equator: like (75,45,15,15,45,75)
#   (actually I like this one best, so it's the default)
def noPolesGetLatitude( x, y ):
	iDiff = CyMap().getTopLatitude() - CyMap().getBottomLatitude()
	hi = float( CyMap().getGridHeight() )
	la = float( y )
	if (not CyMap().isWrapX()) and CyMap().isWrapY():
		hi = float( CyMap().getGridWidth() )
		la = float( x )
	iLat = ( 2 * la + 1 ) * iDiff / ( 2 * hi ) + CyMap().getBottomLatitude()
	return abs( int( round( iLat ) ) )

# get latitude 0..90 for given x,y coordinates - uses build-in function
# - if BtS_3.19 with Jdog's Unofficial Patch 1.00+ is installed:
#   eually distributed, includes poles, but no equator: like (90,54,18,18,54,90)
# - if original 3.19 and earlier version is still used:
#   uses int and has rounding errors (actual values may vary slightly)
#   includes only one pole and equator: like (90,60,30,0,30,60)
def dllGetLatitude( x, y ):
	return map.plot(x,y).getLatitude()

# get latitude 0..90 for given x,y coordinates
# - simulates version from BtS_3.19 with Jdog's Unofficial Patch 1.00+
#   eually distributed, does include poles, but no equator: like (90,54,18,18,54,90)
def floatGetLatitude( x, y ):
	if CyMap().isWrapX() or (not CyMap().isWrapY()):
		iLat = float(y) / (CyMap().getGridHeight() - 1)
	else:
		iLat = float(x) / (CyMap().getGridWidth() - 1)
	iLat = iLat * ( CyMap().getTopLatitude() - CyMap().getBottomLatitude() )
	return abs( int( round( iLat + CyMap().getBottomLatitude() ) ) )

# test if mod dll is patched with 'Unofficial Patch' for 3.19
def checkPatch():
	bPatch = False
	if dllGetLatitude( 0, 0 ) == floatGetLatitude( 0, 0 ):
		if dllGetLatitude( iNumPlotsX-1, iNumPlotsY-1 ) == floatGetLatitude( iNumPlotsX-1, iNumPlotsY-1 ):
			if dllGetLatitude( iNumPlotsX/2, iNumPlotsY/2 ) == floatGetLatitude( iNumPlotsX/2, iNumPlotsY/2 ):
				bPatch = True
	return bPatch

# test if AutoAI is available
def checkAIAuto():
	txt = unicode(CyTranslator().getText("TXT_KEY_AIAUTOPLAY_TURNS", ()))
	return txt.find("AI to control") > -1

# test if BBAI was incorporated into mod
def checkBBAI():
	txt = unicode(CyTranslator().getText("TXT_KEY_MISC_SHIFT_ALT_PREPARE_WAR", ()))
	return txt.find("War Plan") > -1

# test if BUG was incorporated into mod
def checkBUG():
	txt_0 = unicode(CyTranslator().getText("TXT_KEY_BUG_OPTIONS_KEY_REMINDER", ()))
	txt_1 = unicode(CyTranslator().getText("TXT_KEY_BUG_OPTTAB_CREDITS", ()))
	return ( txt_0.find("BUG Mod") > -1 ) or ( txt_1.find("Credits") > -1 )

# test latitude evaluations
def testLatitude():
	sprint  = "[MST] " + "-" * 72 + " testLatitude() ----- \n"
	sprint += "[MST] " + "Coordinates   DLL.getLatitude   Patch.getLatitude   noPolesGetLatitude   evalLatitude \n"
	if map.isWrapX() or (not map.isWrapY()):
		x = 0
		for y in range(iNumPlotsY):
			iLat1 = dllGetLatitude( x, y )				# actual latitude from DLL
			iLat2 = floatGetLatitude( x, y )				# should be latitude (as in UnOffPatch and BBAI)
			iLat3 = noPolesGetLatitude( x, y ) 			# equalized latitude
			iLat4 = evalLatitude( map.plot(x,y) ) 		# evaluated latitude from defLatitude param
			sprint += "[MST] " + "xy: %3i,%2i -> lat1: %2i - %6.3f, lat2: %2i - %6.3f, lat3: %2i - %6.3f,   lat4: %2i - %6.3f \n" % (0,y,iLat1,iLat1/90.0,iLat2,iLat2/90.0,iLat3,iLat3/90.0,iLat4,iLat4/90.0)
	else:
		y = 0
		for x in range(iNumPlotsX):
			iLat1 = dllGetLatitude( x, y )				# actual latitude from DLL
			iLat2 = floatGetLatitude( x, y )				# should be latitude (as in UnOffPatch and BBAI)
			iLat3 = noPolesGetLatitude( x, y ) 			# equalized latitude
			iLat4 = evalLatitude( map.plot(x,y) ) 		# evaluated latitude from defLatitude param
			sprint += "[MST] " + "xy: %3i,%2i -> lat1: %2i - %6.3f, lat2: %2i - %6.3f, lat3: %2i - %6.3f,   lat4: %2i - %6.3f \n" % (x,0,iLat1,iLat1/90.0,iLat2,iLat2/90.0,iLat3,iLat3/90.0,iLat4,iLat4/90.0)
	sprint += "[MST] " + "-" * 72 + " testLatitude() -----"
	print sprint

# test if civ exists in mod
def isCivilization( sInfo ):
	sInfo = "CIVILIZATION_" + sInfo.upper()
	for i in range(gc.getNumCivilizationInfos()):
		info_string = gc.getCivilizationInfo(i).getType()
		if info_string==sInfo: return True
	return False

# test if bonus exists in mod
def isBonus( sInfo ):
	if not (sInfo[0:5] == "BONUS"):
		sInfo = "BONUS_" + sInfo.upper()
	for i in range(gc.getNumBonusInfos()):
		info_string = gc.getBonusInfo(i).getType()
		if info_string==sInfo: return True
	return False

# test if leader exists in mod
def isLeaderHead( sInfo ):
	sInfo = "LEADER_" + sInfo.upper()
	for i in range(gc.getNumLeaderHeadInfos()):
		info_string = gc.getLeaderHeadInfo(i).getType()
		if info_string==sInfo: return True
	return False

# test if mapsize exists in mod
def isWorldSize( sInfo ):
	sInfo = "WORLDSIZE_" + sInfo.upper()
	for i in range(gc.getNumWorldInfos()):
		info_string = gc.getWorldInfo(i).getType()
		if info_string==sInfo: return True
	return False


#####################################################################
########## Common Functions
#####################################################################
# string = space( iSpace )
# string = capWords( str )
# string = strInsert( str, inx, sins )
# bTest = odd( n )
# ab = iif( test, a, b )
# bTest = isList( a )
# printDict( dict, txt = None, prefix = "", cleanUp = True )
# sprint = sprintDict( dict, txt = None )
# printList( lst, txt = None, rows = 5, prefix = "", cleanUp = True )
# sprint = sprintList( lst, txt = None, rows = 5 )
# bFound = removeListElement( aList, elem )
#####################################################################
# return string of spaces
def space( iSpace ):
	return str( " "*iSpace )

# Capitalize all words in string - delimiters are either space or underscore
def capWords(s):
	a = s.split('_')
	for i in range( len(a) ):
		a[i] = (' ').join([x.capitalize() for x in a[i].split(' ')])
	return ('_').join([x for x in a])
#	return (' ').join([x.capitalize() for x in s.split(' ')])

# insert string into another before inx
def strInsert( str, inx, sins ):
	return str[:inx] + sins + str[inx:]

# exchange part of string starting at inx
def strExchange( str, inx, sex ):
	return str[:inx] + sex + str[(inx+len(sex)):]

# test if odd
def odd( n ):
	return ( n%2 != 0 )

# test and pick
# Note: a and b are both evaluated, regardless of the test result
def iif( test, a, b ):
	if test: return a
	return b

# test if parameter is a list
def isList( a ):
	if type(a)==type([]): return True
	return False

# print dictionary nicely
def printDict( dict, txt = None, prefix = "", cleanUp = True ):
	out = sprintDict( dict, txt, prefix )
	if DEBUG:
		stackList = inspect.stack()
		callModule = stackList[1][1]
		callLine = stackList[1][2]
		callFunc = stackList[1][3]
		out = '<<< ' + str( callLine ) + ': ' + callModule + '.' + callFunc + ' >>>\n' + out
	print iif( cleanUp, out.replace("%","%%"), out )

# produce nice dictionary output
def sprintDict( dict, txt = None, prefix="" ):
	sprint = ""
	if not ( type( dict ) == type( {} ) ):
		sprint += prefix + "!! Not a dictionary.\n"
		sprint += prefix + "%s %r" % ( txt, dict )
		return sprint
	if len( dict.keys() ) == 0:
		return prefix + iif( txt==None, "", str(txt) ) + " {}\n"
	sprint += prefix + iif( txt==None, "", str(txt) + "\n" )
	sprint += prefix + " {\n"
	for k in dict.keys():
		sprint += prefix + "   { %r : %r }\n" % ( k, dict[k] )
	sprint += prefix + " }"
	return sprint

# print list nicely
def printList( lst, txt = None, rows = 5, prefix = "", cleanUp = True ):
	out = sprintList( lst, txt, rows, prefix )
	if DEBUG:
		stackList = inspect.stack()
		callModule = stackList[1][1]
		callLine = stackList[1][2]
		callFunc = stackList[1][3]
		out = '<<< ' + str( callLine ) + ': ' + callModule + '.' + callFunc + ' >>>\n' + out
	print iif( cleanUp, out.replace("%","%%"), out )

# produce nice list output
def sprintList( lst, txt = None, rows = 5, prefix = "" ):
	if not ( type( lst ) == type( [] ) ):
		sprint  = prefix + "!! Not a list.\n"
		sprint += prefix + "%s %r" % ( txt, lst )
		return sprint
	if len( lst ) == 0:
		return prefix + iif( txt==None, "", str(txt) ) + " []\n"
	sprint  = prefix + iif( txt==None, "", str(txt) + "\n" )
	sprint += prefix + "["
	cnt = 0
	for k in lst:
		sprint += " %r" % ( k, )
		cnt += 1
		if cnt == len(lst):
			sprint += " ]"
		elif ((cnt % rows) == 0) and ( (cnt < len(lst)-1) or (rows<=1) ):
			sprint += ",\n" + prefix + " "
		else:
			sprint += ","
	return sprint

# remove element from list without raising exception
# use [ data for data in aList if data != elem ] if all elem should be removed
def removeListElement( aList, elem ):
	if aList.count( elem ) > 0:
		aList.remove( elem )
		bFound = True
	else:
		bFound = False
	return bFound


#####################################################
########## Direction Functions
#####################################################
# sName = cardinalName( eCard )
# sName = directionName( eDir )
# eNewDir = getOppositeDirection( eDir )
# eNewDir = addDirection( eDir, index )
# eCardList = getCardDirsFromDir( eDir )
# x,y = xyDirection( eDir )
# x,y = xyCardinalDirection( eCard )
# eDir = coordDirection( x, y, fx, fy )
#####################################################
# get names of cardinal directions
def cardinalName( eCard ):
	if eCard==CardinalDirectionTypes.CARDINALDIRECTION_NORTH: return "North"
	if eCard==CardinalDirectionTypes.CARDINALDIRECTION_EAST:  return "East"
	if eCard==CardinalDirectionTypes.CARDINALDIRECTION_SOUTH: return "South"
	if eCard==CardinalDirectionTypes.CARDINALDIRECTION_WEST:  return "West"
	return "None"

# get names of cardinal directions
def directionName( eDir ):
	if eDir==DirectionTypes.DIRECTION_NORTH:     return "North"
	if eDir==DirectionTypes.DIRECTION_NORTHEAST: return "NorthEast"
	if eDir==DirectionTypes.DIRECTION_EAST:      return "East"
	if eDir==DirectionTypes.DIRECTION_SOUTHEAST: return "SouthEast"
	if eDir==DirectionTypes.DIRECTION_SOUTH:     return "South"
	if eDir==DirectionTypes.DIRECTION_SOUTHWEST: return "SouthWest"
	if eDir==DirectionTypes.DIRECTION_WEST:      return "West"
	if eDir==DirectionTypes.DIRECTION_NORTHWEST: return "NorthWest"
	return "None"

# get opposite direction ( getOppositeCardinalDirection() already exists )
def getOppositeDirection( eDir ):
	return DirectionTypes( (eDir + 4) % 8 )

# add index to direction; clockwise -> positive
def addDirection( eDir, index ):
	iMult, iDir = divmod( eDir + index, 8 )
	return DirectionTypes(iDir)

# get list of the cardinal direction(s) describing a direction
def getCardDirsFromDir( eDir ):
	eCard, check = divmod( eDir, 2 )
	eCardList = [ CardinalDirectionTypes(eCard) ]
	if check == 1:
		eCard += 1
		if eCard == 4: eCard = 0
		eCardList.append( CardinalDirectionTypes(eCard) )
	return eCardList

# get coordinate-change for one step in direction
def xyDirection( eDir ):
	x,y = 0,0
	if   eDir == 0: x,y =  0,-1
	elif eDir == 1: x,y =  1,-1
	elif eDir == 2: x,y =  1, 0
	elif eDir == 3: x,y =  1, 1
	elif eDir == 4: x,y =  0, 1
	elif eDir == 5: x,y = -1, 1
	elif eDir == 6: x,y = -1, 0
	elif eDir == 7: x,y = -1,-1
	return x,y

# get coordinate-change for one step in cardinal direction
def xyCardinalDirection( eCard ):
	x,y = 0,0
	if   eCard == 0: x,y =  0,-1
	elif eCard == 1: x,y =  1, 0
	elif eCard == 2: x,y =  0, 1
	elif eCard == 3: x,y = -1, 0
	return x,y

# get direction from plot x,y toward dx,dy
# ignore wrapping
def coordDirection( x, y, fx, fy ):
	dx = abs(x - fx)
	dy = abs(y - fy)
	if   (x > fx) and (dx >= 2*dy):
		eDir = DirectionTypes.DIRECTION_WEST
	elif (x < fx) and (dx >= 2*dy):
		eDir = DirectionTypes.DIRECTION_EAST
	elif (y > fy) and (dy >= 2*dx):
		eDir = DirectionTypes.DIRECTION_SOUTH
	elif (y < fy) and (dy >= 2*dx):
		eDir = DirectionTypes.DIRECTION_NORTH
	elif (x > fx) and (y > fy):
		eDir = DirectionTypes.DIRECTION_SOUTHWEST
	elif (x > fx) and (y < fy):
		eDir = DirectionTypes.DIRECTION_NORTHWEST
	elif (x < fx) and (y > fy):
		eDir = DirectionTypes.DIRECTION_SOUTHEAST
	elif (x < fx) and (y < fy):
		eDir = DirectionTypes.DIRECTION_NORTHEAST
	else:
		eDir = None					# same plots
	return eDir


##########################################################################################################
########## Mapping Functions
##########################################################################################################
# log = mapSetSign( plot, sTxt, noSign=False, iPlayerNum=None )
# lBorders = getLatitudeBorders( fTundra=0.7, fTaiga=0.6, fDesertTop=0.5, fDesertBottom=0.2, fGrass=0.1,  terGen=None )
# bWater = isHighSeas( x, y, dist=1, data=None, bWrap=False, treshold=0 )
# bWater = isWaterNeighbors( x, y, dist=1, data=None, bWrap=False )
# cnt = numWaterNeighbors( x, y, dist=1, data=None, bWrap=False )
# cnt = numPeakNeighbors( x, y, dist=1, data=None, bWrap=False )
# cnt = numHillNeighbors( x, y, bPeaks=False, dist=1, data=None, bWrap=False )
# cnt = numPlotNeighbors( x, y, ePlotType, dist=1, data=None, bWrap=False )
# cnt = numTerrainNeighbors( x, y, eTerrain, dist=1, data=None, bWrap=False )
# cnt = numFeatureNeighbors( x, y, eFeatures, dist=1, bWrap=False )
# cnt = numNeighborType( x, y, sType, eType, dist=1, bWrap=False )
# bPass = isMountainPass( plot, bStrict=True )
# plot = findPlotNearMountainRange( x, y )
# (eDir0, eDir1) = checkLandBridge( x, y )
# (eDir0, eDir1) = checkDiagonalLandBridge( x, y )
# bWater = isWaterTerrain( eTerrain )
# cntTer = getTerrainPercentage( eTerrain, bPercent=True )
##########################################################################################################

# set landmark/sign at plot
def mapSetSign( plot, sTxt, noSign=False, iPlayerNum=None ):
	signText = CvUtil.convertToStr( sTxt )
	log = ""
	if iPlayerNum == None:
		CyEngine().removeLandmark( plot )
		if not noSign: CyEngine().addLandmark( plot, signText )
	else:
		player = gc.getPlayer( iPlayerNum )
		CyEngine().removeSign( plot, player )
		if not noSign: CyEngine().addSign(plot, player, signText )
		log += " Player %i:" % (player)
	log += " Plot %i,%i named: %s \n" % ( plot.getX(), plot.getY(), sTxt )
	return log

# get list of latitude borders
def getLatitudeBorders( fTundra=0.7, fTaiga=0.6, fDesertTop=0.5, fDesertBottom=0.2, fGrass=0.1, terGen=None ):
	try:
		lBorders = [ terGen.fTundraLatitude, terGen.fTaigaLatitude, terGen.fDesertTopLatitude, \
					 terGen.fDesertBottomLatitude, terGen.fGrassLatitude ]
#		print "terrainGenerator BorderLatitudes: %r" % (lBorders)
	except:
		fTundra += gc.getClimateInfo(map.getClimate()).getSnowLatitudeChange() #must keep getSnow, comes from API
		fTundra = min(fTundra, 1.0)
		fTundra = max(fTundra, 0.0)

		fTaiga += gc.getClimateInfo(map.getClimate()).getTundraLatitudeChange() #must keep getTundra, comes from API
		fTaiga = min(fTaiga, 1.0)
		fTaiga = max(fTaiga, 0.0)

		fDesertTop += gc.getClimateInfo(map.getClimate()).getDesertTopLatitudeChange()
		fDesertTop = min(fDesertTop, 1.0)
		fDesertTop = max(fDesertTop, 0.0)

		fDesertBottom += gc.getClimateInfo(map.getClimate()).getDesertBottomLatitudeChange()
		fDesertBottom = min(fDesertBottom, 1.0)
		fDesertBottom = max(fDesertBottom, 0.0)

		fGrass += gc.getClimateInfo(map.getClimate()).getGrassLatitudeChange()
		fGrass = min(fGrass, 1.0)
		fGrass = max(fGrass, 0.0)

		lBorders = [ fTundra, fTaiga, fDesertTop, fDesertBottom, fGrass]
#		print "default BorderLatitudes: %r" % (lBorders)
	return lBorders

# check if there are (or more than treshold) any non-water plots in the vicinity; excluding the center spot
# tests plot at opposite end of map, if plot falls beyond the edge
def isHighSeas( x, y, dist=1, data=None, bWrap=False, treshold=0 ):
	cnt = 0
	for dx in range( -dist, dist+1 ):
		for dy in range( -dist, dist+1 ):
			if (dx == 0) and (dy == 0): continue
			if bWrap:
				# if not wrapped, ignore plots on the other side of the map
				xx, yy = normalizeXY( x, y )
				if not map.isWrapX():
					if (xx+dx)<0 or (xx+dx)>=iNumPlotsX: continue
				if not map.isWrapY():
					if (yy+dy)<0 or (yy+dy)>=iNumPlotsY: continue
			if data==None:
				plot = GetPlot( x+dx, y+dy )
				if not plot.isWater():
					if treshold == cnt: return False
					cnt += 1
			else:
				i = GetIndex( x+dx, y+dy )
				if not data[i] == PlotTypes.PLOT_OCEAN:
					if treshold == cnt: return False
					cnt += 1
	return True

# count how much water is in the neighborhood; excluding the center plot
# tests plot at opposite end of map, if plot falls beyond the edge
def numWaterNeighbors( x, y, dist=1, data=None, bWrap=False ):
	return numPlotNeighbors( x, y, PlotTypes.PLOT_OCEAN, dist, data, bWrap )

# count how much water is in the neighborhood; excluding the center plot
# tests plot at opposite end of map, if plot falls beyond the edge
def numPeakNeighbors( x, y, dist=1, data=None, bWrap=False ):
	return numPlotNeighbors( x, y, PlotTypes.PLOT_PEAK, dist, data, bWrap )

# count how many hills (and evtl. peaks) are in the neighborhood; excluding the center plot
# tests plot at opposite end of map, if plot falls beyond the edge (adjustable via bWrap)
def numHillNeighbors( x, y, bPeak=False, dist=1, data=None, bWrap=False ):
	cnt = 0
	for dx in range( -dist, dist+1 ):
		for dy in range( -dist, dist+1 ):
			if (dx == 0) and (dy == 0): continue
			if bWrap:
				# don't count plots on the other side of the map
				xx, yy = normalizeXY( x, y )
				if not map.isWrapX():
					if (xx+dx)<0 or (xx+dx)>=iNumPlotsX: continue
				if not map.isWrapY():
					if (yy+dy)<0 or (yy+dy)>=iNumPlotsY: continue
			if data == None:
				plot = GetPlot( x+dx, y+dy )
				if plot.isHills(): cnt += 1
				elif bPeak and plot.isPeak(): cnt += 1
			else:
				i = GetIndex( x+dx, y+dy )
				if data[i] == PlotTypes.PLOT_HILLS: cnt += 1
				elif bPeak and (data[i] == PlotTypes.PLOT_PEAK): cnt += 1
	return cnt

# count how many plots of given plotType are in the neighborhood; excluding the center spot
# tests plot at opposite end of map, if plot falls beyond the edge (adjustable via bWrap)
def numPlotNeighbors( x, y, ePlotType, dist=1, data=None, bWrap=False ):
	cnt = 0
	for dx in range( -dist, dist+1 ):
		for dy in range( -dist, dist+1 ):
			if (dx == 0) and (dy == 0): continue
			if bWrap:
				# don't count plots on the other side of the map
				xx, yy = normalizeXY( x, y )
				if not map.isWrapX():
					if (xx+dx)<0 or (xx+dx)>=iNumPlotsX: continue
				if not map.isWrapY():
					if (yy+dy)<0 or (yy+dy)>=iNumPlotsY: continue
			if data == None:
				plot = GetPlot( x+dx, y+dy )
				if plot.getPlotType() == ePlotType:
					cnt += 1
			else:
				i = GetIndex( x+dx, y+dy )
				if data[i] == ePlotType:
					cnt += 1
	return cnt

# count how many plots of given terrain are in the neighborhood; excluding the center spot
# tests plot at opposite end of map, if plot falls beyond the edge
def numTerrainNeighbors( x, y, eTerrain, dist=1, data=None, bWrap=False ):
	cnt = 0
	for dx in range( -dist, dist+1 ):
		for dy in range( -dist, dist+1 ):
			if (dx == 0) and (dy == 0): continue
			if bWrap:
				# don't count plots on the other side of the map
				xx, yy = normalizeXY( x, y )
				if not map.isWrapX():
					if (xx+dx)<0 or (xx+dx)>=iNumPlotsX: continue
				if not map.isWrapY():
					if (yy+dy)<0 or (yy+dy)>=iNumPlotsY: continue
			if data == None:
				plot = GetPlot( x+dx, y+dy )
				if plot.getTerrainType() == eTerrain:
					cnt += 1
			else:
				i = GetIndex( x+dx, y+dy )
				if data[i] == eTerrain:
					cnt += 1
	return cnt

# count how many plots of given feature(s) are in the neighborhood; excluding the center spot
# tests plot at opposite end of map, if plot falls beyond the edge
# eFeatures may be a single eFeature of a list of eFeatures to be tested against
def numFeatureNeighbors( x, y, eFeatures, dist=1, bWrap=False ):
	if isList( eFeatures ):
		fList = eFeatures
	else:
		fList = [ eFeatures ]
	cnt = 0
	for dx in range( -dist, dist+1 ):
		for dy in range( -dist, dist+1 ):
			if (dx == 0) and (dy == 0): continue
			if bWrap:
				# don't count plots on the other side of the map
				xx, yy = normalizeXY( x, y )
				if not map.isWrapX():
					if (xx+dx)<0 or (xx+dx)>=iNumPlotsX: continue
				if not map.isWrapY():
					if (yy+dy)<0 or (yy+dy)>=iNumPlotsY: continue
			plot = GetPlot( x+dx, y+dy )
			if plot.getFeatureType() in fList:
				cnt += 1
	return cnt

# count how many plots of given type are in the neighborhood; excluding the center spot
# tests plot at opposite end of map, if plot falls beyond the edge
# available for sType: 'TERRAIN', 'FEATURE', 'BONUS#, 'IMPROVEMENT', 'LAKE'
def numNeighborType( x, y, sType, eType, dist=1, bWrap=False ):
	cnt = 0
	for dx in range( -dist, dist+1 ):
		for dy in range( -dist, dist+1 ):
			if (dx == 0) and (dy == 0): continue
			if bWrap:
				# don't count plots on the other side of the map
				xx, yy = normalizeXY( x, y )
				if not map.isWrapX():
					if (xx+dx)<0 or (xx+dx)>=iNumPlotsX: continue
				if not map.isWrapY():
					if (yy+dy)<0 or (yy+dy)>=iNumPlotsY: continue
			i = GetIndex( x+dx, y+dy )
			plot = map.plotByIndex( i )
			if sType.upper() == 'TERRAIN':
				if plot.getTerrainType() == eType:
					cnt += 1
			elif sType.upper() == 'FEATURE':
				if plot.getFeatureType() == eType:
					cnt += 1
			elif sType.upper() == 'BONUS':
				if plot.getBonusType(-1) == eType:
					cnt += 1
			elif sType.upper() == 'IMPROVEMENT':
				if plot.getImprovementType() == eType:
					cnt += 1
			elif sType.upper() == 'LAKE':
				if plot.isLake():
					cnt += 1
	return cnt

# check if plot is mountain-pass
# - not bStrict: has two mountain neighbors, which are separated by at least two direction steps
# - bStrict:     has two mountain neighbors in two cardinal directions
# - has a way in and a way out
def isMountainPass( plot, bStrict=True ):
	x,y = plot.getX(), plot.getY()
	mountDir = None
	bWayIn = False
	bWayOut = False
	bPass = False
	for eDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
		pl = plotDirection( x, y, DirectionTypes(eDir) )
		if pl.isNone(): continue
		if pl.isPeak():
			if not odd( eDir ):
				if mountDir == None:							# first mountain?
					mountDir = eDir
					bWayOut = False
				else:
					if abs(eDir - mountDir) == 2:
						p = plotDirection( x, y, DirectionTypes(eDir-1) )
						if p.isNone(): continue
						if p.isFlatlands() or p.isHills():
							return True						# small pass found
					elif abs(eDir - mountDir) == 6:
						p = plotDirection( x, y, DirectionTypes(eDir+1) )
						if p.isNone(): continue
						if p.isFlatlands() or p.isHills():
							return True						# small pass found
					else:
						bPass = True
		elif not pl.isWater():
			if mountDir == None:								# first mountain?
				bWayIn = True
			elif bPass:
				bWayIn = True
			else:
				bWayOut = True
	if ( bWayIn and bPass and bWayOut ):
		return True
	# 2nd chance if not bStrict
	if not bStrict:
		mountDir = None
		bWayIn = False
		bWayOut = False
		bPass = False
		for eDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
			pl = plotDirection( x, y, DirectionTypes(eDir) )
			if pl.isNone(): continue
			if pl.isPeak():
				if mountDir == None:							# first mountain?
					mountDir = eDir
				else:
					if abs(eDir - mountDir) == 1:			# peaks adjacent
						mountDir = eDir
					elif abs(eDir - mountDir) == 2:		# peaks one step away
						bWayOut = True
					else:
						bWayOut = True
						bPass = True
			elif not pl.isWater():
				if mountDir == None:							# first mountain?
					bWayIn = True
				elif bPass:
					bWayIn = True
	return ( bWayIn and bPass and bWayOut )

# distance to nearest starting-plot
def startingPlotDistance( x, y ):
	playerList = [ gc.getPlayer( playerID ) for playerID in range( gc.getMAX_CIV_PLAYERS() )
											 if gc.getPlayer( playerID ).isAlive() ]
	sPlotList = [ player.getStartingPlot() for player in playerList ]
	minDist = 99999
	for pl in sPlotList:
		dx,dy = pl.getX(), pl.getY()
		dist = plotDistance( x, y, dx, dy )
		if dist < minDist:
			minDist = dist
	return minDist

# prepare to move mountain - find potential plot to move to; doesn't check center-plot
def findPlotNearMountainRange( x, y ):
	ringDist = 2
	pHeight = []
	for dx in range(-ringDist, 1+ringDist):
		for dy in range(-ringDist, 1+ringDist):
			pDist = plotDistance( x, y, x+dx, y+dy )
			if pDist == ringDist:
				plot = plotXY( x, y, dx, dy)
				if not plot.isNone():
					if plot.isFlatlands():
						n = numHillNeighbors( dx, dy, True )
						for i in range(n):
							pHeight.append( plot )
	# return plot or None if empty
	return chooseListElement( pHeight )

# Check if tile is a land-bridge.
# Return connecting land-plots or None.
# A land-bridge is a tile connecting two parts of a land-area.
def checkLandBridge( x, y ):
	dirList = []
	cnt = 0
	for eDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
		pl = plotDirection( x, y, DirectionTypes(eDir) )
		if pl.isNone(): continue
		if not pl.isWater():
			if cnt > 1: return None
			cnt += 1
			dirList.append( eDir )
	if len( dirList ) != 2: return None
	d = dirList[1] - dirList[0]
	if ( d < 2 ) or ( d > 6 ): return None
	return (dirList[0], dirList[1])

# Check if tile is a diagonal land-bridge.
# Return connecting land-plots or None.
# ---------------------------------------------------------
# A diagonal land-bridge is a tile
# diagonally connecting two parts of a land-area.
#
# ........   or   ........	   Note that only      .........
# .xxx....        .xxx....    the nearby          .xxxx....
# .xxx....        .xxx....    tiles are           .x.xx....
# ....O...        ....O...    analyzed.           .x...O...
# .....xx.        ..xx....                        .xx...xx.
# .....xx.        ...xxx..    This is a diag.     .xxxxxxx.
# ........        ........    land-bridge too:    .........
# ---------------------------------------------------------
def checkDiagonalLandBridge( x, y ):
	dirList = []
	for eDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
		pl = plotDirection( x, y, DirectionTypes(eDir) )
		if pl.isNone(): return None
		if not pl.isWater():
			if not odd( eDir ): return None
			dirList.append( eDir )
	if len( dirList ) != 2: return None
	return (dirList[0], dirList[1])

# check if terrain needs water-plot - like coast
def isWaterTerrain( eTerrain ):
	return gc.getTerrainInfo( eTerrain ).isWater()

# get number of plots which have a specific terrain
# return either the absolute number or a percentage of land / water, depending on terrain
def getTerrainPercentage( eTerrain, bPercent=True ):
	cntWater = 0
	cntTer = 0
	for inx in range( map.numPlots() ):
		plot = map.plotByIndex( inx )
		ter = plot.getTerrainType()
		if plot.isWater(): cntWater += 1
		if ter == eTerrain: cntTer += 1
	if bPercent:
		if isWaterTerrain( eTerrain ):
			return round( ( (cntTer * 100.0) / cntWater ), 2 )
		else:
			return round( ( (cntTer * 100.0) / (map.numPlots() - cntWater) ), 2 )
	else:
		return cntTer


################################################################################
########## Area Functions
################################################################################
# regionCoordList = getRegion( areaData=None, iSurround=0 )
# areaPlots = getAreaPlots( areaID=None, isValidFn = None )
# areaCoords = getAreaPlotsXY( areaID=None, isValidFn = None )
# coastPlots = getContinentCoast( continentPlots, bLakes=False )
# coastCoords = getContinentCoastXY( continentPlots, bLakes=False )
# minDist = getContinentDistance( areaID, otherAreaID=None )
# topAreas = getBigAreas( iTop, bCoord=True, noGoAreaPlots=None, iMinPlots=30 )
# ----------------------------------------
# Already implemented area civ4-functions
# ----------------------------------------
# map.recalculateAreas()
# areaID = plot.getArea()
# areaID = area.getID()
# area = plot.area()
# area = map.getArea( areaID )
# area = map.findBiggestArea( bWater )
# bTest = plot.isAdjacentToArea( area )
# areaList = CvMapGeneratorUtil.getAreas()
################################################################################

# get region from area
# - the region is the smallest rectangle surrounding the area
# - areaData may be an actual areaID or a tupel (x0,x1,y0,y1)
# - support wrapping around the edges: x0, y0 may be negative
# - ensure that always x0 <= x1 and y0 <= y1
def getRegion( areaData=None, iSurround=0 ):
	x0 = 0
	x1 = iNumPlotsX - 1
	y0 = 0
	y1 = iNumPlotsY - 1
	if areaData != None:
		if type( areaData ) == type( () ):
			# areaData already representing the region
			x0, x1, y0, y1 = areaData
		elif type( areaData ) == type( 0 ):
			# areaData is areaID
			xDict = {}
			yDict = {}
			for x in range( iNumPlotsX ):
				for y in range( iNumPlotsY ):
					pl = map.plot( x, y )
					if areaData == pl.getArea():
						xDict[ x ] = True
						yDict[ y ] = True
			xList = xDict.keys()
			x0 = min( xList )
			x1 = max( xList )
			if ( 0 in xList ) and ( (iNumPlotsX-1) in xList ) and ( len( xList ) != iNumPlotsX ):
				diffList = [ d for d in range( iNumPlotsX ) if d not in xList ]
				x0 = max( diffList ) + 1
				x1 = min( diffList ) - 1
			yList = yDict.keys()
			y0 = min( yList )
			y1 = max( yList )
			if ( 0 in yList ) and ( (iNumPlotsY-1) in yList ) and ( len( yList ) != iNumPlotsY ):
				diffList = [ d for d in range( iNumPlotsY ) if d not in yList ]
				y0 = max( diffList ) + 1
				y1 = min( diffList ) - 1
		# expand region into surrounding tiles
		if iSurround > 0:
			x0 = max( 0, x0 - iSurround )
			x1 = min( iNumPlotsX - 1, x1 + iSurround )
			y0 = max( 0, y0 - iSurround )
			y1 = min( iNumPlotsY - 1, y1 + iSurround )
		# ensure that x0 <= x1 and y0 <= y1
		if x0 > x1: x0 = x0 - iNumPlotsX
		if y0 > y1: y0 = y0 - iNumPlotsY
	return [x0, x1, y0, y1]

# get all plots from area; if no area is given, get all land-plots
# returns a list of plots
def getAreaPlots( areaID=None, isValidFn = None ):
	areaPlots = []
	for i in range( map.numPlots() ):
		plot = map.plotByIndex(i)
		if areaID == None:
			if plot.isWater(): continue
		else:
			if plot.getArea() != areaID: continue
		if isValidFn != None:
			if not isValidFn( plot ): continue
		areaPlots.append( plot )
	return areaPlots

# get all plots from area; if no area is given, get all land-plots
# returns a list of coordinate-pairs
def getAreaPlotsXY( areaID=None, isValidFn = None ):
	areaPlots = getAreaPlots( areaID, isValidFn )
	areaCoords = [ ( plot.getX(), plot.getY() ) for plot in areaPlots ]
	return areaCoords

# get list of coastal plots around continent; if bLakes then inside lakes are included
# continentPlots may be a list of either plots or coordinate pairs (x,y)
# returns list of plots
def getContinentCoast( continentPlots, bLakes=False ):
	coastPlots = []
	if len( continentPlots ) == 0: return coastPlots
	if type( continentPlots[0] ) == type( () ):
		conPlots = continentPlots
	else:
		conPlots = [ ( plot.getX(), plot.getY() ) for plot in continentPlots ]
	for x,y in conPlots:
		for eDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
			p = plotDirection( x, y, DirectionTypes(eDir) )
			if p.isNone(): continue
			if p.isWater():
				if p.isLake() and ( not bLakes ): continue
				if p.getTerrainType() == etCoast:
					if p not in coastPlots:
						coastPlots.append( p )
	return coastPlots

# get list of coastal plots around continent; if bLakes then inside lakes are included
# returns list of coordinate-pairs
def getContinentCoastXY( continentPlots, bLakes=False ):
	coastPlots = getContinentCoast( continentPlots, bLakes )
	coastCoords = [ ( plot.getX(), plot.getY() ) for plot in coastPlots ]
	return coastCoords

# get the shortest distance between continents
# if 2nd continent is not given, then the distance to
# the nearest other continent is returned
def getContinentDistance( areaID, otherAreaID=None ):
	if areaID == otherAreaID: return 0
	# get 1st area
	area = map.getArea( areaID )
	if area.isWater(): return -1
	aPlotList = getAreaPlots( areaID )
	if len(aPlotList) == 0: return -1
	aCoastList = getContinentCoastXY( aPlotList )
	if len(aCoastList) == 0:
		aCoastList = getContinentCoastXY( aPlotList, True )
	# get 2nd area
	if otherAreaID == None:
		# get coast of all other continents
		otherCoastList = []
		for inx in range( map.numPlots() ):
			pl = map.plotByIndex( inx )
			if pl.isCoastalLand():
				if pl.getArea() != areaID:
					x,y = coordByPlot( pl )
					otherCoastList.append( (x,y) )
	else:
		# get coast of given continent
		otherArea = map.getArea( otherAreaID )
		if otherArea.isWater(): return -1
		otherPlotList = getAreaPlots( otherAreaID )
		if len(otherPlotList) == 0: return -1
		otherCoastList = getContinentCoastXY( otherPlotList )
		if len(otherCoastList) == 0:
			aCoastList = getContinentCoastXY( otherPlotList, True )
	# get minimum distance
	minDist = 99999
	for x,y in aCoastList:
		for dx,dy in otherCoastList:
			dist = stepDistance(x,y,dx,dy)
			if dist < minDist:
				minDist = dist
			if minDist <= 2:
				return minDist
	return minDist

# get list of biggest land areas with their plots [iNumPlots, iAreaID, plotList]
# plotList is either a list of plots of coordinate-tuples
def getBigAreas( iTop, bCoord=True, noGoAreaPlots=None, iMinPlots=30 ):
	CyMap().recalculateAreas()
	continentArea = []
	areas = CvMapGeneratorUtil.getAreas()
	if not (noGoAreaPlots == None):
		if len( noGoAreaPlots ) == 0:
			noGoAreaPlotList = []
		else:
			if type( noGoAreaPlots[0] ) == type( () ):
				noGoAreaPlotList = [ GetPlot(x, y) for x,y in noGoAreaPlots ]
			else:
				noGoAreaPlotList = noGoAreaPlots
	for area in areas:
		if area.isWater(): continue
		if area.getNumTiles() < iMinPlots: continue
		iAreaID = area.getID()
		# check for forbidden areas
		bTaboo = False
		if not (noGoAreaPlots == None):
			for tabooPlot in noGoAreaPlotList:
				if tabooPlot.getArea() == iAreaID:
					bTaboo = True
					break
		if bTaboo: continue
		# add to list of continents
		if bCoord:
			areaPlotList = getAreaPlotsXY( iAreaID )
		else:
			areaPlotList = getAreaPlots( iAreaID )
		continentArea.append( [len(areaPlotList), area.getID(), areaPlotList] )
	continentArea = [ cont for cont in continentArea if cont[0] > 0 ]
	continentArea.sort()
	return continentArea[0:iTop]


################################################################################
########## Coordinate, Plot and Index Conversions
################################################################################
# plot = GetPlot(x,y)				# same as plot = map.plot(x,y), but AutoWrap					#
# inx = GetIndex(x,y)				# same as inx = map.plotNum(x,y), but AutoWrap
# xx,yy = coordByPlot( plot )
# xx,yy = coordByIndex( inx )
# inx = indexByPlot( plot )
# inx = map.plotNum(x,y)			# regular civ4 function
# plot = map.plotByIndex( inx ) 	# regular civ4 function
# plot = map.plot(x,y)				# regular civ4 function
# xx,yy = normalizeXY(x,y)
################################################################################

# convert x and y to a plot (Auto-Wrap)
# allways gives usable plot
def GetPlot(x,y):
	xx, yy = normalizeXY( x, y )
	return map.plot( xx, yy )

# convert x and y to an index (Auto-Wrap)
# allways gives usable index
def GetIndex(x,y):
	xx, yy = normalizeXY( x, y )
	return ( yy * iNumPlotsX + xx )

# get plot-coordinates from plot
def coordByPlot( plot ):
	if plot == None: return -1, -1
	if plot.isNone(): return -1, -1
	return plot.getX(), plot.getY()

# get plot-coordinates from index
def coordByIndex( inx ):
	if (inx < 0) or (inx > map.numPlots()): return -1, -1
	yy, xx = divmod( inx, iNumPlotsX )
	return xx, yy

# get plot-index from plot
def indexByPlot( plot ):
	if plot == None: return -1
	if plot.isNone(): return -1
	return ( plot.getY() * iNumPlotsX + plot.getX() )

# make sure x,y are within map-range (Auto-Wrap)
def normalizeXY( x, y ):
	xx = x % iNumPlotsX
	yy = y % iNumPlotsY
	return xx, yy


##################################################################################
########## Randomizing Functions
##################################################################################
# ab = choose(iPercent, a, b)
# xValue = chooseMore( *t )
# elem = chooseDictElement( aDict )
# elem = chooseListElement( aList )
# elem = chooseListIndex( aList )
# elem = chooseListPop( aList )
# iNum = chooseNumber( iRand, iMax=None )
##################################################################################

# choose with iPercent chance
def choose( iPercent, a, b ):
	iRand = dice.get(100, "MapTools.choose()")
	if iRand<iPercent: return a
	return b

# choose from several (iPercent,xValue) tuples; iPercent ascending toward 100%
# parameter may be also a list of tuples
# Usage:
# bon = chooseMore( (10,"BONUS_SILVER"), (35,"BONUS_GOLD"), (50,"BONUS_COPPER"), (85,"BONUS_IRON") )
# will give the boni names with 10%, 25%, 15% and 35% probability or None with 15% probability
def chooseMore( *t ):
	iRand = dice.get(100, "MapScriptTools.chooseMore()")
	li = []
	if len(t)==1:
		li = t[0]
	elif len(t) > 0:
		li = t
	for i in range( len(li) ):
		iPercent, xValue = li[i]
		if iRand<iPercent:
			return xValue
	return None

# randomly pick item from dictionary
def chooseDictElement( aDict ):
	if len(aDict)==0: return None
	aList = aDict.keys()
	iRand = dice.get( len(aList), "MapScriptTools.chooseDictElement()" )
	return aDict[ aList[iRand] ]

# randomly pick item from list
def chooseListElement( aList ):
	if len(aList)==0: return None
	iRand = dice.get( len(aList), "MapScriptTools.chooseListElement()" )
	return aList[ iRand ]

# randomly pick index from list
def chooseListIndex( aList ):
	if len(aList)==0: return -1
	iRand = dice.get( len(aList), "MapScriptTools.chooseListIndex()" )
	return iRand

# randomly pick index from list, delete index and return element
def chooseListPop( aList ):
	if len(aList)==0: return None
	iRand = dice.get( len(aList), "MapScriptTools.chooseListPop()" )
	return aList.pop( iRand )

# get random number within [0 .. iRand-1] or [iRand .. iMax-1]
def chooseNumber( iRand, iMax=None ):
	if iMax == None: iMax, iRand = iRand, 0
	if iMax < iRand: iMax, iRand = iRand, iMax
	iDice = iMax - iRand
	return dice.get( iDice, "MapScriptTools.chooseNumber()" ) + iRand


#######################################################################################
### CLASS RandomList - randomize lists
#######################################################################################
# newList = xshuffle( oriList )
# shuffle( oriList )
# countList = randomCountList( count )
#######################################################################################

# get shuffled lists
class RandomList:
	# return new shuffled list - don't change original
	def xshuffle( self, oriList ):
		size = len( oriList )
		if size <= 1:
			return list( oriList )
		else:
			preList = list( oriList )
			newList = []
			while size:
				iChoose = chooseNumber( size )
				newList.append( preList[iChoose] )
				preList[iChoose] = preList[size-1]
				size -= 1
		return newList

	# shuffle original list - only change the original, no return
	def shuffle( self, oriList ):
		size = len( oriList )
		if size > 1:
			oriList.append( None )
			while size:
				iChoose = chooseNumber( size )
				oriList[size] = oriList[iChoose]
				oriList[iChoose] = oriList[size-1]
				size -= 1
			del oriList[0]

	# return shuffled list of numbers from 0 .. count-1
	def randomCountList( self, count ):
		cList = [ i for i in range(count) ]
		return self.xshuffle( cList )

#######################################################################################
### CLASS RandomList END
#######################################################################################
randomList = RandomList()


############################################################################
### CLASS CivFolders - check registry to find civ and mod files
############################################################################
# Class Variables (Example):
# --- always accessible
# appName:    Beyond the Sword
# userDir:    ....\My Documents\My Games
# rootDir:    ....\My Documents\My Games\Beyond the Sword
# logDir:     ....\My Documents\My Games\Beyond the Sword\Logs
# appDir:     ..\Civilization 4\Beyond the Sword
# --- accessible only after calling getModPaths()
# modDir:     ..\Civilization 4\Beyond the Sword\Mods\Rise of Mankind
# modName:    Rise of Mankind
# modFolder:  Mods\Rise of Mankind
############################################################################
# getModPaths()
# --- private ---
# getCivPaths()
############################################################################
class CivFolders:

	# class vars
	appName = "Beyond the Sword"
	logDir = None
	rootDir = None
	appDir = None
	userDir = None
	modName = None
	modFolder = None
	modDir = None

	def __init__( self ):
		print "[MST] " + "===== initialize Class::CivFolders"
		self.getCivPaths()

	# get path for actual mod
	# - this function can't go into __init__() since replay won't be ready
	def getModPaths( self ):
		print "[MST] " + "===== civFolders.getModPaths()"

		# get modName and modFolder
		self.modDir = None
		try:
			from CvPythonExtensions import CyReplayInfo
			replay = CyReplayInfo()
			replay.createInfo( 0 )
			mod = replay.getModName()
			self.modFolder = os.path.normpath( mod )
			mDir, self.modName = os.path.split( self.modFolder )

			if self.modName=='Hills':
				self.modName = "No Mod"
				self.modFolder = None
		except:
			self.modName = "? Unknown Mod"

		# get modDir
		if self.rootDir!=None and self.modFolder!=None and self.modName!=None:
			mod = os.path.join( self.rootDir, self.modFolder, self.modName + ".ini" )
			if (os.path.isfile( mod )):
				self.modDir = os.path.join( self.rootDir, self.modFolder )
			else:
				if self.appDir!=None and self.modFolder!=None and self.modName!=None:
					mod = os.path.join( self.appDir, self.modFolder, self.modName + ".ini" )
					if (os.path.isfile( mod )):
						self.modDir = os.path.join( self.appDir, self.modFolder )
					else:
						self.modDir = None
		sprint = "\n"
		sprint += "[MST] ------------------------------------ civFolders:getModPaths ---\n"
		sprint += "[MST] " + "modDir:    %s\n" % (self.modDir)
		sprint += "[MST] " + "modName:   %s\n" % (self.modName)
		sprint += "[MST] " + "modFolder: %s\n" % (self.modFolder)
		sprint += "[MST] ---------------------------------------------------------------"
		print sprint

	###############
	### Helpers ###
	###############

	# get paths for civ
	def getCivPaths( self ):
		print "[MST] " + "===== civFolders.getCivPaths()"
		try:
			import CvAltRoot
			if os.path.isdir( CvAltRoot.rootDir ):
				if os.path.isfile( os.path.join(CvAltRoot.rootDir, "CivilizationIV.ini") ):
					self.rootDir = CvAltRoot.rootDir
					print "[MST] " + "Overriding rootDir using CvAltRoot!"
				else:
					print "[MST] " + "Cannot find CivilizationIV.ini in directory from CvAltRoot.py"
			else:
				print "[MST] " + "Directory from CvAltRoot.py is not valid"
		except:
			pass

		if self.rootDir:
			self.userDir = os.path.dirname( self.rootDir )
		else:
			# Determine the base user directory (e.g. "C:\...\My Documents\My Games").
			self.userDir = None
			if (sys.platform == 'darwin'):
				"Mac OS X"
				self.userDir = os.path.join(os.environ['HOME'], "Documents")
			else:
				import _winreg
				"Windows"
				#############################################
				def __getRegValue(root, subkey, name):
					key = _winreg.OpenKey(root, subkey)
					try:
						value = _winreg.QueryValueEx(key, name)
						return value[0]
					finally:
						key.Close()
				#############################################

				myDocuments = None
				try:
					myDocuments = __getRegValue(_winreg.HKEY_CURRENT_USER,
							r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
							"Personal")
				except:
					try:
						# Vista
						myDocuments = __getRegValue(_winreg.HKEY_CURRENT_USER,
								r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
								"Personal")
					except:
						pass

				if myDocuments is None:
					print "[MST] " + "Cannot find My Documents folder registry key"
					self.userDir = "\\"
				else:
					self.userDir = os.path.join(myDocuments, "My Games")

		# Determine the root directory that holds the executable and mods
		# as well as the directory inside "My Games" that holds CustomAssets and mods.
		if ( sys.executable ):
			self.appDir = os.path.dirname( sys.executable )
			self.appName = os.path.basename( self.appDir )
		else:
			print "[MST] " + "No executable ??"

		if self.rootDir is None:
			self.rootDir = os.path.join( self.userDir, self.appName )
		self.logDir = os.path.join( self.rootDir, "Logs" )
		sprint  = "[MST] ------------------------------------ civFolders:getCivPaths ---\n"
		sprint += "[MST] " + "appName: %s\n" % (self.appName)
		sprint += "[MST] " + "userDir: %s\n" % (self.userDir)
		sprint += "[MST] " + "rootDir: %s\n" % (self.rootDir)
		sprint += "[MST] " + "logDir:  %s\n" % (self.logDir)
		sprint += "[MST] " + "appDir:  %s\n" % (self.appDir)
		sprint += "[MST] ---------------------------------------------------------------"
		print sprint

#######################################################################################
### CLASS CivFolders END
#######################################################################################
civFolders = CivFolders()


#######################################################################################
### CLASS DeepOcean - put Deep Ocean onto map
#######################################################################################
# buildDeepOcean( dist=3, chDeep=80 )
#######################################################################################
class DeepOcean:

	# put Deep Ocean in the middle of the worlds oceans, if supported by mod
	# - don't do it with Planetfall
	def buildDeepOcean( self, dist=4, chDeep=75 ):
		if not bOceanDeep: return
		if bPfall or bMars: return
		print "[MST] ===== DeepOcean:buildDeepOcean()"

		deepList = []
		for x in range( iNumPlotsX ):
			for y in range( iNumPlotsY ):
				if isHighSeas( x, y, dist, bWrap=True ):
					if choose( chDeep, True, False ):
						plot = map.plot( x, y )
						plot.setTerrainType( etOceanDeep, False, False )
						deepList.append( plot )

		for passes in [1,2,3]:
			for pl in deepList:
				x,y = coordByPlot( pl )
				eCard = chooseNumber( 4 )
				p = plotCardinalDirection( x, y, CardinalDirectionTypes(eCard) )
				if p.isNone(): continue
				if p.getTerrainType() == etOcean:
					if choose( chDeep/(passes+1), True, False ):
						p.setTerrainType( etOceanDeep, False, False )
						deepList.append( p )

		print "[MST] %i plots with Deep Ocean terrain built" % ( len(deepList) )

#######################################################################################
### CLASS DeepOcean END
#######################################################################################
deepOcean = DeepOcean()


#######################################################################################
### CLASS PlanetFallMap - adjust map for use with Planetfall-Mod
#######################################################################################
# buildPfallOcean()
# pFallTerrain = mapPfallTerrain( eTerrain, terList, plot, terrainGen=None )
# buildPfallHighlands( iBaseChance=None )
# --- private ---
# moveLonlyHills()
# buildPfallShelfAndTrenches( chShelf=50, chTrench=45 )
# adjustShelfTrenches()
# cnt = numTrenchNeighbors( x, y, dist=1 )
# ok = setTrench( plot )
# getValidTrenchTerrain()
#######################################################################################
class PlanetFallMap:

	validTrenchTerrain = []

	# put shelfs and trenches into ocean
	def buildPfallOcean( self, chShelf=45, chTrench=45 ):
		if not bPfall: return
		print "[MST] ===== PlanetFallMap:buildPfallOcean()"

		# build trenches and shelves
		self.buildPfallShelfAndTrenches( chShelf, chTrench )			# default: slightly less shelves
		# prettify trenches and shelves
		self.adjustShelfTrenches()

	# give eTerrain and latitude of plot (0.0 .. 1.0), get pfallTerrain
	def mapPfallTerrain( self, eTerrain, terList, plot, terrainGen=None ):
#		print "[MST] ===== PlanetFallMap:mapToPfallTerrain)"

		# get latitude ranges
		latList = getLatitudeBorders( terGen=terrainGen )
		pLatitude = evalLatitude( plot, False )						# 0 .. 1

		fTundra   = latList[0]
		fTaiga = latList[1]
		fDesBot = latList[2]
		fDesTop = latList[3]
		fGrass  = latList[4]

		itOcean  = terList[0]
		itCoast  = terList[1]
		itDesert = terList[2]
		itPlains = terList[3]
		itGrass  = terList[4]
		itMarsh  = terList[5]
		itTaiga = terList[6]
		itTundra   = terList[7]

		pfallTerrain = etOcean
		if eTerrain==itDesert:   pfallTerrain = choose( 66, etFlatArid, etRockyArid )
		elif eTerrain==itPlains: pfallTerrain = choose( 66, etFlatMoist, etRockyMoist )
		elif eTerrain==itGrass:  pfallTerrain = choose( 66, etFlatRainy, etRockyRainy )
		elif eTerrain==itMarsh:  pfallTerrain = etFlatRainy
		elif eTerrain==itTaiga: pfallTerrain = choose( 66, etRockyMoist, etFlatPolar )
		elif eTerrain==itTundra:   pfallTerrain = choose( 66, etFlatPolar, etRockyPolar )
		elif eTerrain==itCoast:  pfallTerrain = etCoast

		if pfallTerrain==etRockyArid and pLatitude<fDesBot: pfallTerrain = choose( 66, etRockyMoist, etRockyArid )
		elif pfallTerrain==etFlatArid and pLatitude<fDesBot: pfallTerrain = choose( 66, etFlatMoist, etFlatArid )
		elif pfallTerrain==etRockyArid and pLatitude>fDesTop: pfallTerrain = choose( 66, etRockyMoist, etRockyArid )
		elif pfallTerrain==etFlatArid and pLatitude>fDesTop: pfallTerrain = choose( 66, etFlatMoist, etFlatArid )
		elif pfallTerrain==etFlatRainy and pLatitude>fDesBot and pLatitude<fDesTop: pfallTerrain = choose( 80, etFlatRainy, etFlatMoist )
		elif pfallTerrain==etFlatPolar and pLatitude<fDesTop: pfallTerrain = choose( 80, etRockyMoist, etFlatMoist )
		elif pfallTerrain==etFlatPolar and pLatitude<fTaiga: pfallTerrain = choose( 80, etRockyMoist, etFlatPolar )
		elif pfallTerrain==etFlatPolar and pLatitude<fTundra: pfallTerrain = choose( 66, etRockyMoist, etFlatPolar )
		elif pfallTerrain==etRockyPolar and pLatitude<fTaiga: pfallTerrain = etRockyMoist
		elif pfallTerrain==etRockyPolar and pLatitude<fTundra: pfallTerrain = choose( 66, etFlatPolar, etRockyPolar )
		return pfallTerrain

	# build Highlands and Foothills using existing peaks and hills as seeder
	def buildPfallHighlands( self, iBaseChance=None ):
		if not bPfall: return
		print "[MST] ===== PlanetFallMap:buildPfallHighlands()"

		aPlots = mapStats.statPlotCount( " ----- PlanetFallMap.buildPfallHighlands() before -----" )
		iChance = 35 - aPlots[1] - aPlots[2]						# fHills, fPeaks
		iChance = min( 33, iChance )
		iChance = max(  1, iChance )
		chBase = iChance
		if iBaseChance != None:											# give basechance depending on stats
			iChance = iBaseChance										# given basechance

		iMult = 4															# default size multiplier
		if sClimateType=="CLIMATE_ROCKY": iMult += 1
		if sSeaType=="SEALEVEL_LOW": iMult += 1

		nChance = int( (iChance + 4*map.getWorldSize()) * iMult / 10 )
		print "[MST] iChance: %4.2f, iMult %i -> nChance %i" % (iChance, iMult, nChance)
		print "[MST] default: chBase: %4.2f, iMult %i -> nChance %i" % (chBase, iMult, int((chBase+4*map.getWorldSize())*iMult/10 ))

		# pass 1 - build highlands and foothills
		cntH = 0
		cntP = 0
		for x in range( iNumPlotsX ):
			for y in range( iNumPlotsY ):
				plot = plotXY( x, y, 0, 0 )
				if plot.isHills() or plot.isPeak():
					for iDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
						p = plotDirection( x, y, DirectionTypes(iDir) )
						if p.isNone(): continue
						if p.isFlatlands():
							if choose( nChance, True, False ):
								p.setPlotType( PlotTypes.PLOT_HILLS, True, True )
#								print "[MST] Flat -> Hills  @ %i,%i" % ( p.getX(), p.getY() )
								cntH += 1
						elif p.isHills():
							if choose( nChance/2, True, False ):
								p.setPlotType( PlotTypes.PLOT_PEAK, True, True )
#								print "[MST] Hills -> Peak  @ %i,%i" % ( p.getX(), p.getY() )
								cntP += 1
		sprint = "[MST] Changed Pass-1: Flat->Hill %i,  Hill->Peak %i, nChance: %i \n" % (cntH, cntP, nChance)
		cntH, cntP = 0, 0

		# pass 2 - do it some more for foothills
		for x in range(iNumPlotsX):
			for y in range(iNumPlotsY):
				plot = plotXY(x,y,0,0)
				if plot.isFlatlands():
					iHills = numHillNeighbors( x, y )
					nChance = iHills * iHills * iHills / 3
					if choose( nChance, True, False ):
						plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
#						print "[MST] Flat -> Hills  @ %i,%i - 2nd pass" % ( p.getX(), p.getY() )
						cntH += 1
		sprint += "[MST] Changed Pass-2: Flat->Hill %i,  Hill->Peak %i, nChance: %i \n" % (cntH, cntP, nChance)
		print sprint
		self.moveLonlyHills() 	# improve valleys
		aPlots = mapStats.statPlotCount( " ----- PlanetFallMap.buildPfallHighlands() after -----" )

	###############
	### Helpers ###
	###############

	# move single hills (or mountains) into ranges
	def moveLonlyHills( self ):
		print "[MST] ======== PlanetFallMap:moveLonlyHills()"
		nChance = 80
		cntH = 0
		sprint = ""
		for x in range(iNumPlotsX):
			for y in range(iNumPlotsY):
				plot = plotXY(x,y,0,0)
				if plot.isWater() or plot.isFlatlands(): continue
				if numHillNeighbors( x, y, True ) == 0:
					pl = findPlotNearMountainRange( x, y )
					if pl != None:
#						print "[MST] chance to move hill/peak to %i,%i" % (pl.getX(), pl.getY())
						if choose( nChance, True, False ):
							pType = plot.getPlotType()
							plot.setPlotType( PlotTypes.PLOT_LAND, True, True )
							pl.setPlotType( pType, True, True )
							cntH += 1
							sprint += "[MST] single hill/peak moved to @ %i,%i \n" % (pl.getX(),pl.getY())
		if cntH>0:
			sprint += "[MST] Moved %i lonely Hills/Mountains toward ranges, nChance: %i \n" % (cntH, nChance)
		else:
			sprint += "[MST] No lonely mountains moved \n"
		print sprint

	# builds trenches and shelves on 'Planetfall' ocean
	# >>> algorithm taken from Planetfall.py <<<
	def buildPfallShelfAndTrenches( self, chShelf=45, chTrench=45 ):
		if not bPfall: return
		print "[MST] ======== PlanetFallMap:buildPfallShelfAndTrenches()"

		self.getValidTrenchTerrain()

		prob_base = 1.00
		prob_shelf = 0
		prob_mod = 0.30
		prob_spawn = -0.30
		prob_trench = chTrench / 100.0

		for x in range( iNumPlotsX ):
			for y in range( iNumPlotsY ):
				plot = map.plot( x, y )
				if plot.isNone(): continue
				if plot.getTerrainType() not in self.validTrenchTerrain: continue
				if plot.isLake(): continue									# no trenches/shelves in lakes

				# try to avoid inland trenches or shelves
				if numWaterNeighbors(x, y, 1) <  5: continue
				if numWaterNeighbors(x, y, 2) < 13: continue

				ocean_counter = 0
				trench_counter = 0
				highland_counter = 0
				prob_drop = 0.0

				for iDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
					p = plotDirection( x, y, DirectionTypes(iDir) )
					if p.isNone(): continue
					if p.isWater(): ocean_counter += 1
					if p.isHills(): highland_counter += 1
					if p.isPeak():  highland_counter += 1
					if self.isTrench( p ):
						trench_counter += 1
					if p.getTerrainType() in self.validTrenchTerrain:
						prob_drop = prob_drop * prob_mod + prob_mod

				prob = prob_base - prob_drop
				if( trench_counter == 0 ):   prob = prob + prob_spawn
				elif( trench_counter == 1 ): prob = prob + prob_trench
				elif( trench_counter > 2 ):  prob = 0
				if( ocean_counter == 0 ):    prob = 0
				if( highland_counter == 0 ): prob = 0

				if choose( prob*100, True, False ):						# trench lines
					self.setTrench( plot )

		for x in range( iNumPlotsX ):
			for y in range( iNumPlotsY ):
				plot = map.plot( x, y )
				if plot.isNone(): continue
				if plot.getTerrainType() != etOcean: continue
				prob_shelf = 0

				for iDir in range( DirectionTypes.NUM_DIRECTION_TYPES ):
					p = plotDirection( x, y, DirectionTypes(iDir) )
					if p.isNone(): continue
					if not p.isWater(): continue
					if not self.isTrench( p ):
						if p.getTerrainType() in [etCoast, etShelf]:
							prob_shelf = chShelf

				if choose( prob_shelf, True, False ):						# shelf extension
					plot.setTerrainType( etShelf, True, True )

	# connect diagonal trenches and kill isolated shelves or trenches
	def adjustShelfTrenches( self ):
		if not bPfall: return
		print "[MST] ======== PlanetFallMap:adjustShelfTrenches()"
		cntKillShelves = 0
		cntKillTrenches = 0
		cntAddTrenches = 0

		# kill orphan shelves
		for x in range( iNumPlotsX ):
			for y in range( iNumPlotsY ):
				plot = map.plot( x, y )
				if plot.getTerrainType() == etShelf:
					terCnt = numTerrainNeighbors( x, y, etShelf )
					if terCnt == 0:
						plot.setTerrainType( etOcean, True, True )
						cntKillShelves += 1

		# trenchify diagonal trench-connections
		for x in range( iNumPlotsX ):
			for y in range( iNumPlotsY ):
				plot = map.plot( x, y )
				if self.isTrench( plot ):
					# diagonal directions
					diagDirSet = set( [1, 3, 5, 7] )
					# cardinal directions
					for eDir in [0, 2, 4, 6]:
						pl = plotDirection( x, y, DirectionTypes(eDir) )
						if pl.isNone(): continue
						if self.isTrench( pl ):
							diag1 = (eDir + 8 - 1) % 8
							diag2 = (eDir + 8 + 1) % 8
							diagDirSet -= set( [diag1, diag2] )
					# remaining diagonal directions
					for eDir in diagDirSet:
						pl = plotDirection( x, y, DirectionTypes(eDir) )
						if pl.isNone(): continue
						if self.isTrench( pl ):
							card1 = (eDir + 8 - 1) % 8
							card2 = (eDir + 8 + 1) % 8
							cardList = [ card1, card2 ]
							buildList = []
							bTrench = False
							for eCard in cardList:
								p = plotDirection( x, y, DirectionTypes(eCard) )
								if self.isTrench( p ):
									bTrench = True
									break
								if p.getTerrainType() in self.validTrenchTerrain:
									buildList.append( eCard )
							if not bTrench:
								if len( buildList ) > 0:
									eCard = chooseListElement( buildList )
									p = plotDirection( x, y, DirectionTypes(eCard) )
									self.setTrench( p )
									cntAddTrenches += 1

		# kill orphan trenches
		for x in range( iNumPlotsX ):
			for y in range( iNumPlotsY ):
				plot = map.plot( x, y )
				if self.isTrench( plot ):
					terCnt = self.numTrenchNeighbors(x, y)
					if terCnt == 0:
						if plot.getFeatureType() == efTrench:
							plot.setFeatureType( FeatureTypes.NO_FEATURE, -1 )
							cntKillTrenches += 1
						elif plot.getImprovementType() == eiTrench:
							plot.setImprovementType( ImprovementTypes.NO_IMPROVEMENT )
							cntKillTrenches += 1
		print "[MST] Connected %i Trenches - Eliminated isolated Shelves: %i, Trenches: %i" % (cntAddTrenches, cntKillShelves, cntKillTrenches)

	# number of trenches surrounding the plot; excluding center
	def numTrenchNeighbors( self, x, y, dist=1 ):
#		print "[MST] ======== PlanetFallMap:numTrenchNeighbors()"
		cnt = 0
		for dx in range( x-dist, x+dist+1 ):
			for dy in range( y-dist, y+dist+1 ):
				if (dx == x) and (dy == y): continue
				plot = map.plot(dx, dy)
				if plot.getTerrainType() == etTrench:
					cnt += 1
				elif plot.getFeatureType() == efTrench:
					cnt += 1
				elif plot.getImprovementType() == eiTrench:
					cnt += 1
		return cnt

	def isTrench( self, plot ):
#		print "[MST] ======== PlanetFallMap:isTrench()"
		return ( (plot.getFeatureType() == efTrench) or (plot.getImprovementType() == eiTrench) )

	def setTrench( self, plot ):
#		print "[MST] ======== PlanetFallMap:setTrench()"
		# set trench if terrain is valid
		ok = false
		ter = plot.getTerrainType()
		if ter in self.validTrenchTerrain:
			feat = plot.getFeatureType()
			if feat == efIce:
				plot.setImprovementType( eiTrench )
				ok = True
			else:
				# trumps all other features
				plot.setFeatureType( efTrench, -1 )
				ok = True
		return ok

	# get valid terrains for FEATURE_TRENCH
	def getValidTrenchTerrain( self ):
		print "[MST] ======== PlanetFallMap:getValidTrenchTerrain()"
		self.validTrenchTerrain = []
		for i in range( gc.getNumTerrainInfos() ):
			if gc.getFeatureInfo( efTrench ).isTerrain( i ):
				self.validTrenchTerrain.append( i )


#######################################################################################
### CLASS PlanetFallMap END
#######################################################################################
planetFallMap = PlanetFallMap()


#####################################################################################
### CLASS MapPrettifier - small changes to beautify you map
#####################################################################################
# connectifyLakes( chConnect=75 )
# deIcifyEdges( iLat=66, addToroidIce=True )
# hillifyCoast( chHills=66 )
# beautifyVolcanos( chHills=66 )
# lumpifyTerrain( targetTerrain, sourceTer1, sourceTer2=None )
# bulkifyIslands( chConnect=66, maxIsle=4 )
# percentifyTerrain( targetTerTuple, *sourceTerTuples )
# percentifyPlots( targetPlotType, fTargetPlotPercent, data=None, terGenerator=None )
# --- private ---
# (p1, p2) = checkDiagonalWater( x, y, eDiagoDir )
#####################################################################################
class MapPrettifier:

	# connect different lakes which are only diagonally disconnected
	# may change small single-plot lakes to Land/Hills instead of connecting
	# use after generatePlotTypes()
	def connectifyLakes( self, chConnect=75 ):
		print "[MST] ===== MapPrettifier:connectifyLakes()"
		wCnt = 0
		lCnt = 0
		edList = [ DirectionTypes.DIRECTION_NORTHWEST, DirectionTypes.DIRECTION_NORTHEAST,
				   DirectionTypes.DIRECTION_SOUTHEAST, DirectionTypes.DIRECTION_SOUTHEAST ]
		for x in range( 1, iNumPlotsX-1 ):
			map.recalculateAreas()
			for y in range( 1, iNumPlotsY-1 ):
				plot = map.plot(x, y)
				if not plot.isWater(): continue
				for eDir in edList:
					cardPlots = self.checkDiagonalWater( x, y, eDir )
					if not cardPlots: continue
					pl = plotDirection(x, y, eDir)
					if pl.isNone(): continue
					if plot.getArea() == pl.getArea(): continue
					if riverMaker.hasRiverAtPlot( plot ): continue
					if riverMaker.hasRiverAtPlot( pl ): continue
					# now we have a landbridge without rivers separating two lakes
					if (map.getArea(plot.getArea()).getNumTiles() == 1):
						if choose(chConnect, True, False):
							plot.setPlotType( choose(90,PlotTypes.PLOT_LAND,PlotTypes.PLOT_HILLS), False, False)
							lCnt += 1
							break
					elif (map.getArea(pl.getArea()).getNumTiles() == 1):
						if choose(chConnect, True, False):
							pl.setPlotType( choose(90,PlotTypes.PLOT_LAND,PlotTypes.PLOT_HILLS), False, False)
							lCnt += 1
					else:
						randomList.shuffle( cardPlots )
						for p in cardPlots:
							if choose( chConnect, True, False ):
								p.setPlotType( PlotTypes.PLOT_OCEAN, False, False)
								#map.recalculateAreas()  # we choose speed over precision here
								wCnt += 1
		print "[MST] %i lakes connected and %i single-plot lakes filled in" % ( wCnt, lCnt )

	# kill water-ice on non-polar edge
	# - only works if called after or at the end of normalizeAddExtras()
	def deIcifyEdges( self, iLat=66, addToroidIce=True ):
		print "[MST] ===== MapPrettifier:deIcifyEdges()"
		if not map.isWrapY():
			# deIcify SouthPole and southern hemisphere
			if evalLatitude( map.plot(0,0), True ) < iLat:
				print "[MST] DeIcify the south between %i and %i" % (0, iNumPlotsY/2 - 1)
				for x in range( iNumPlotsX ):
					for y in range( iNumPlotsY / 2 ):
						plot = map.plot( x, y )
						if plot.getFeatureType() == efIce:
							if not plot.isPeak():
								plot.setFeatureType( FeatureTypes.NO_FEATURE, -1 )
			# deIcify NorthPole and northern hemisphere
			if evalLatitude( map.plot(iNumPlotsX-1, iNumPlotsY-1) ) < iLat:
				print "[MST] DeIcify the north between %i and %i" % ((iNumPlotsY-1)/2, iNumPlotsY-1)
				for x in range( iNumPlotsX ):
					for y in range( (iNumPlotsY-1)/2, iNumPlotsY ):
						plot = map.plot( x, y )
						if plot.getFeatureType() == efIce:
							if not plot.isPeak():
								plot.setFeatureType( FeatureTypes.NO_FEATURE, -1 )
		# put some ice on the polar waters on toroid shaped worlds
		if addToroidIce:
			if	map.isWrapX() and map.isWrapY():
				cnt = 0
				for inx in range( map.numPlots() ):
					plot = map.plotByIndex( inx )
					lat = evalLatitude( plot ) + chooseNumber(13) - 6					# random drift
					# Ice only beyond at least 65 degrees latitude
					if lat > 65:
						if plot.isWater():
							if plot.getFeatureType() == FeatureTypes.NO_FEATURE:
								if plot.getBonusType(-1) == BonusTypes.NO_BONUS:
									if plot.canHaveFeature( efIce ):
										x,y = coordByIndex( inx )
										nIce  = numFeatureNeighbors(x, y, efIce)
										if bPfall:
											nIce += numTerrainNeighbors(x, y, etFlatPolar)
											nIce += numTerrainNeighbors(x, y, etRockyPolar)
										else:
											nIce += numTerrainNeighbors(x, y, etTundra)
										ch = (110 - lat) * 2 - (nIce * 5)
										if map.getClimate() == 1: ch += 12						# tropical
										if map.getClimate() == 4: ch -= 12						# cold
										if choose( ch, False, True ):
											plot.setFeatureType( efIce, -1 )
											cnt += 1
				# bulkify ice
				cnt1, cnt2 = 0, 0
				chIceKill = 33
				chIceAdd  = 75
				zone = [ (0,2), (2,0), (0,-2), (1,2), (2,1), (1,-2), (2,-1) ]
				for passes in [1,2]:
					for inx in range( map.numPlots() ):
						plot = map.plotByIndex( inx )
						x,y = coordByIndex( inx )
						if not plot.isWater(): continue
						if plot.getFeatureType() == efIce:
							if numFeatureNeighbors( x,y, efIce, dist=1 ) == 0:
								if choose( chIceKill, True, False ):
									plot.setFeatureType( FeatureTypes.NO_FEATURE, -1 )
									cnt1 += 1
								else:
									iceList = [ plotXY(x,y,dx/2,dy/2) for dx,dy in zone
																				 if ( plotXY(x,y,dx,dy).isWater() ) and
																					( plotXY(x,y,dx,dy).getBonusType(-1) == -1 ) and
																					( plotXY(x,y,dx,dy).getFeatureType() == efIce ) ]
									pl = chooseListElement( iceList )
									if pl == None: continue
									if choose( chIceAdd, True, False ):
										pl.setFeatureType( efIce, -1 )
										cnt2 += 1
				print "[MST] Put %i ice tiles on toroid world" % (cnt)
				print "[MST] Killed %i ice tiles on toroid world" % (cnt1)
				print "[MST] Added %i ice tiles on toroid world" % (cnt2)

	# change peaks on coast to hills
	def hillifyCoast( self, chHills=66 ):
		if bPfall or bMars: return
		print "[MST] ===== MapPrettifier:hillifyCoast()"
		iCnt = 0
		x0 = iif( map.isWrapX(), 0, 1 )
		x1 = iif( map.isWrapX(), iNumPlotsX, iNumPlotsX-1 )
		y0 = iif( map.isWrapY(), 0, 1 )
		y1 = iif( map.isWrapY(), iNumPlotsY, iNumPlotsY-1 )
		for x in range( x0, x1 ):
			for y in range( y0, y1 ):
				pl = map.plot(x, y)
				if pl.isPeak() and pl.isCoastalLand():
					if pl.getFeatureType() < 0:					# don't transform volcanos
						if choose( chHills, True, False ):
							# If a peak is along the coast, change to hills and recalc.
							pl.setPlotType(PlotTypes.PLOT_HILLS, True, True)
							iCnt += 1
		print "[MST] %i coastal peaks transformed to hills" % ( iCnt )

	# change volcanos on coast to hills / peaks - they really look bad sometimes
	def beautifyVolcanos( self, chHills=66 ):
		if bPfall or bMars: return
		print "[MST] ===== MapPrettifier:beautifyVolcanos()"
		if not bVolcano: return
		cntVol = 0
		cntHill = 0
		x0 = iif( map.isWrapX(), 0, 1 )
		x1 = iif( map.isWrapX(), iNumPlotsX, iNumPlotsX-1 )
		y0 = iif( map.isWrapY(), 0, 1 )
		y1 = iif( map.isWrapY(), iNumPlotsY, iNumPlotsY-1 )
		for x in range( x0, x1 ):
			for y in range( y0, y1 ):
				cnt = 0
				plot = map.plot(x, y)
				if plot.getFeatureType() == efVolcano:
					for eCard in range( CardinalDirectionTypes.NUM_CARDINALDIRECTION_TYPES ):
						p = plotCardinalDirection( x, y, CardinalDirectionTypes(eCard) )
						if p.isNone(): continue
						if p.isWater(): cnt += 1
					if cnt > 1:
						plot.setFeatureType( FeatureTypes.NO_FEATURE, -1 )
						cntVol += 1
						if choose( chHills, True, False ):
							plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
							cntHill += 1
		if cntVol > 0: print "[MST] %i coastal volcanos eliminated and %i coastal peaks transformed to hills" % ( cntVol,cntHill )

	# change plains/grass surrounded by desert to desert; or any other terrain combinations
	def lumpifyTerrain( self, targetTerrain, sourceTer1, sourceTer2=None ):
		print "[MST] ===== MapPrettifier:lumpifyTerrain()"
		cnt = 0
		chChange = 40
		passes = [1]
		if not bPfall:
			if (targetTerrain == etDesert) and (map.getClimate() == 2): passes.append(2)		# arid climate
			elif (targetTerrain == etGrass) and (map.getClimate() == 1): passes.append(2)		# tropical climate
		for pa in passes:
			for x in range( iNumPlotsX ):
				for y in range( iNumPlotsY ):
					plot = map.plot( x, y )
					if plot.getTerrainType() == sourceTer1:
						tarNum = numTerrainNeighbors( x, y, targetTerrain )
						if tarNum > 3:
							if choose( chChange + 4*tarNum, True, False):
								plot.setTerrainType( targetTerrain, True, True )
								cnt += 1
					elif plot.getTerrainType() == sourceTer2:
						tarNum = numTerrainNeighbors( x, y, targetTerrain )
						if tarNum > 4:
							if choose( chChange/2 + 3*tarNum, True, False):
								plot.setTerrainType( targetTerrain, True, True )
								cnt += 1
		if cnt > 0: print "[MST] %i terrains lumpified" % ( cnt )

	# connect small islands; at least some islands of the chain should be bigger
	# builds hills/peaks - to be used before addRivers()
	def bulkifyIslands( self, chConnect=66, maxIsle=4 ):
		print "[MST] ===== MapPrettifier:bulkifyIslands()"
		cnt = 0
		for inx in range( map.numPlots() ):
			plot = map.plotByIndex( inx )
			x,y = coordByIndex( inx )
			if plot.isWater(): continue								# islands!
			area = plot.area()
			id = plot.getArea()
			if area.getNumTiles() > maxIsle: continue				# to big
			for dx,dy in [ (0,2), (2,0), (-2,0), (0,-2) ]:
				pl = plotXY( x, y, dx, dy )
				if pl.isNone(): continue								# no plot
				if pl.isWater(): continue								# islands!
				if pl.area().getNumTiles() > maxIsle: continue	# to big
				if pl.getArea() == id: continue						# same island
				if choose( chConnect, True, False ):
					p = plotXY( x, y, dx/2, dy/2 )
					pType = chooseMore( (66, PlotTypes.PLOT_LAND), (90, PlotTypes.PLOT_HILLS), (100, PlotTypes.PLOT_PEAK) )
					p.setPlotType( pType, True, True )
					if choose( 66, True, False ):
						p = plotXY( x, y, iif(dx==0,1,dx/2), iif(dy==0,1,dy/2) )
						pType = chooseMore( (66, PlotTypes.PLOT_LAND), (90, PlotTypes.PLOT_HILLS), (100, PlotTypes.PLOT_PEAK) )
						p.setPlotType( pType, True, True )
					if choose( 66, True, False ):
						p = plotXY( x, y, iif(dx==0,-1,dx/2), iif(dy==0,-1,dy/2) )
						pType = chooseMore( (66, PlotTypes.PLOT_LAND), (90, PlotTypes.PLOT_HILLS), (100, PlotTypes.PLOT_PEAK) )
						p.setPlotType( pType, True, True )
					cnt += 1
					break
			for dx,dy in [ (1,2), (2,1), (-2,1), (1,-2), (-1,2), (2,-1), (-2,-1), (-1,-2) ]:
				pl = plotXY( x, y, dx, dy )
				if pl.isNone(): continue								# no plot
				if pl.isWater(): continue								# islands!
				if pl.area().getNumTiles() > maxIsle: continue	# to big
				if pl.getArea() == id: continue						# same island
				if choose( chConnect, True, False ):
					p0 = GetPlot( x + dx/2, y + dy/2 )
					p1 = choose( 50, GetPlot( x + dx, y + dy/2), GetPlot(x + dx/2, y + dy) )
					pType0 = chooseMore( (66, PlotTypes.PLOT_LAND), (90, PlotTypes.PLOT_HILLS), (100, PlotTypes.PLOT_PEAK) )
					pType1 = chooseMore( (66, PlotTypes.PLOT_LAND), (90, PlotTypes.PLOT_HILLS), (100, PlotTypes.PLOT_PEAK) )
					p0.setPlotType( pType0, True, True )
					p1.setPlotType( pType1, True, True )
					cnt += 1
					break
		print "[MST] %i small islands connected" % ( cnt )

	# specify a terrain and its appearance-percentage on the map
	# either as percent of land or as percent of water, depending on terrain
	# - if too much of this terrain already exists on the map, some of it will change
	#   into the source terrains according to the chances given in the source-tuples
	# - if there is not enough of this terrain on the map already, some of the surrounding
	#   source terrains given will be converted to the target terrain
	# - some seed terrain needs to be already on the map
	# - example: percentifyTerrain( (etTaiga,5), (etGrass,12), (etTundra,2), (etMarsh,3) )
	#   changes grass,snow,marsh into tundra or splits tundra into grass,snow,marsh
	def percentifyTerrain( self, targetTerTuple, *sourceTerTuples ):
		print "[MST] ===== MapPrettifier:percentifyTerrain()"
		# check parameter
		if len( sourceTerTuples ) == 0:
			print "[MST] No source terrains given."
			return
		# read parameter
		eTerrain, chPercent = targetTerTuple
		bWater = isWaterTerrain( eTerrain )
		srcTer = []
		chTer = []
		for i in range( len(sourceTerTuples) ):
			srcTerrain, srcChance = sourceTerTuples[i]
			# we don't change plots
			if isWaterTerrain( srcTerrain ) == bWater:
				srcTer.append( srcTerrain )
				chTer.append( srcChance )
		# check seed terrain
		cntTer = 0
		for inx in range( map.numPlots() ):
			plot = map.plotByIndex( inx )
			if eTerrain == plot.getTerrainType():
				cntTer += 1
		if cntTer == 0:
			print "[MST] No seed terrain on map."
			return
		# calc cummulative change chances
		ch = 0
		for iChance in chTer: ch += iChance
		fMult = 100.0 / ch
		srcChList = []
		for i in range( len(chTer) ):
			chTer[i] = int( round(chTer[i] * fMult) )
			srcChList.append( (chTer[i], srcTer[i]) )
		# five passes if necessary
		passes = [0,1,2,3,4]
		for loop in passes:
			print " - pass %i" % (loop)
			# count things, make lists
			cntWater = 0
			cntTer = 0
			terList = []
			srcList = []
			for inx in range( map.numPlots() ):
				plot = map.plotByIndex( inx )
				ter = plot.getTerrainType()
				if plot.isWater(): cntWater += 1
				if ter == eTerrain:
					cntTer += 1
					if numTerrainNeighbors( plot.getX(), plot.getY(), eTerrain ) < (3+loop):
						if choose( 33, True, False ):
							terList.append( inx )
				elif ter in srcTer:
					if numTerrainNeighbors( plot.getX(), plot.getY(), eTerrain ) > (4-loop):
						if choose( 33, True, False ):
							srcList.append( inx )
			# more or less
			baseTer = iif( bWater, cntWater, map.numPlots()-cntWater )
			wantTer = baseTer * chPercent / 100
			if loop == 0:
				print "[MST] Target percentage: %i, Terrain percentage before: %4.2f(%i)" % (chPercent,cntTer*100.0/baseTer,cntTer)
				if ( abs(wantTer-cntTer) * 100.0 / baseTer ) <= 0.5:
					print "[MST] Target percentage already reached."
					return
			if	wantTer < cntTer:
				# have too many already
				randomList.shuffle( terList )
				for inx in terList:
					newTer = chooseMore( srcChList )
					if not (newTer == None):
						plot = map.plotByIndex( inx )
						# make sure there are no marshy hills
						if plot.isHills():
							if bMarsh:
								if newTer == etMarsh:
									continue
						plot.setTerrainType( newTer, True, True )
						cntTer -= 1
						if	wantTer == cntTer:
							print "[MST] Target percentage reached. \n Target percentage: %i, Terrain percentage after %i passes: %4.2f(%i)" % (chPercent,loop+1,cntTer*100.0/baseTer,cntTer)
							return
			else:
				# need some more
				randomList.shuffle( srcList )
				for inx in srcList:
					plot = map.plotByIndex( inx )
					# make sure there are no marshy hills
					if plot.isHills():
						if bMarsh:
							if eTerrain == etMarsh:
								continue
					plot.setTerrainType( eTerrain, True, True )
					cntTer += 1
					if	wantTer == cntTer:
						print "[MST] Target percentage reached. \n Target percentage: %i, Terrain percentage after %i passes: %4.2f(%i)" % (chPercent,loop+1,cntTer*100.0/baseTer,cntTer)
						return
		print "[MST] Target percentage: %i, Terrain percentage after %i passes: %4.2f(%i)" % (chPercent,loop,cntTer*100.0/baseTer,cntTer)

	# specify a plotType and its appearancePercentage on the map
	# - PlotTypes.PLOT_OCEAN will convert from or into PlotTypes.PLOT_LAND
	# - PlotTypes.PLOT_LAND will convert from or into PlotTypes.PLOT_OCEAN
	# - PlotTypes.PLOT_HILLS will convert from or into PlotTypes.PLOT_LAND
	# - PlotTypes.PLOT_PEAK will convert from or into PlotTypes.PLOT_HILLS
	# - some seed plots need to be already on the map
	def percentifyPlots( self, targetPlotType, fTargetPlotPercent, data=None, terGenerator=None ):
		print "[MST] ===== MapPrettifier:percentifyPlots()"
		sourceDict = 	{
							PlotTypes.PLOT_OCEAN : PlotTypes.PLOT_LAND,
							PlotTypes.PLOT_LAND : PlotTypes.PLOT_OCEAN,
							PlotTypes.PLOT_HILLS : PlotTypes.PLOT_LAND,
							PlotTypes.PLOT_PEAK : PlotTypes.PLOT_HILLS
							}

		# check seed plots (more than 3)
		cntPlot = 0
		for inx in range( map.numPlots() ):
			if data == None:
				plot = map.plotByIndex( inx )
				pType = plot.getPlotType()
			else:
				pType = data[inx]
			if targetPlotType == pType:
				cntPlot += 1
		if cntPlot < 4:
			print "[MST] Not enough seeds on map."
			return data
		# five passes if necessary
		src = sourceDict[ targetPlotType ]
		print "[MST] Target %r, Source %r" % (targetPlotType, src)
		passes = [0,1,2,3,4]
		for loop in passes:
			print " - pass %i" % (loop)
			# count things, make lists
			cntPlot = 0
			plotList = []
			srcList = []
			for inx in range( map.numPlots() ):
				x, y = coordByIndex(	inx )
				if data == None:
					plot = map.plotByIndex( inx )
					plType = plot.getPlotType()
				else:
					plType = data[inx]
				if plType == targetPlotType:
					cntPlot += 1
					if numPlotNeighbors( x, y, targetPlotType ) < (3+loop):
						if choose( 33, True, False ):
							plotList.append( inx )
				elif plType == src:
					if numPlotNeighbors( x, y, targetPlotType ) > (4-loop):
						if choose( 33, True, False ):
							srcList.append( inx )
			# more or less
			wantPlots = int( map.numPlots() * fTargetPlotPercent / 100.0 )
			if loop == 0:
				print "[MST] Target percentage: %4.2f, plotType percentage before: %4.2f(%i)" % (fTargetPlotPercent,cntPlot*100.0/map.numPlots(),cntPlot)
				if ( abs(wantPlots-cntPlot) * 100.0 / wantPlots ) <= 0.5:
					print "[MST] Target percentage already reached."
					return data
			if	wantPlots < cntPlot:
				# have too many already
				randomList.shuffle( plotList )
				for inx in plotList:
					if data==None:
						plot = map.plotByIndex( inx )
						plot.setPlotType( src, False, False )
						if terGenerator != None:
							x,y = coordByPlot( plot )
							terGenerator.generateTerrainAtPlot(x, y)
					else:
						data[inx] = src
					cntPlot -= 1
					if	abs(wantPlots - cntPlot) <= 1:
						print "[MST] Target percentage reached. \n Target percentage: %4.2f, PlotType percentage after %i passes: %4.2f(%i)" % (fTargetPlotPercent,loop+1,cntPlot*100.0/map.numPlots(),cntPlot)
						return data
			else:
				# need some more
				randomList.shuffle( srcList )
				for inx in srcList:
					if data==None:
						plot = map.plotByIndex( inx )
						plot.setPlotType( targetPlotType, False, False )
						if terGenerator != None:
							x,y = coordByPlot( plot )
							terGenerator.generateTerrainAtPlot(x, y)
					else:
						data[inx] = targetPlotType
					cntPlot += 1
					if	abs(wantPlots - cntPlot) <= 1:
						print "[MST] Target percentage reached. \n Target percentage: %4.2f, PlotType percentage after %i passes: %4.2f(%i)" % (fTargetPlotPercent,loop+1,cntPlot*100.0/map.numPlots(),cntPlot)
						return data
		print "[MST] Target percentage: %4.2f, PlotType percentage after %i passes: %4.2f(%i)" % (fTargetPlotPercent,loop,cntPlot*100.0/map.numPlots(),cntPlot)
		return data

	###############
	### Helpers ###
	###############

	# check diagonal plots for water, return related cardinal plots if both of those are land or None
	# (x,y) is not checked!
	def checkDiagonalWater( self, x, y, eDir ):
#		print "[MST] ======== MapPrettifier:checkDiagonalWater()"
		if map.plot(x, y).getPlotType() != PlotTypes.PLOT_OCEAN: return None
		x0,y0 = xyDirection( eDir )
		p = plotXY(x, y, x0, y0)
		if p.isNone(): return None
		if p.getPlotType() != PlotTypes.PLOT_OCEAN: return None
		plot0 = plotXY(x, y, x0, 0)
		plot1 = plotXY(x, y, 0, y0)
		if plot0.getPlotType() == PlotTypes.PLOT_OCEAN: return None
		if plot1.getPlotType() == PlotTypes.PLOT_OCEAN: return None
		return [ plot0, plot1 ]


####################################################################
### CLASS MapPrettifer END
####################################################################
mapPrettifier = MapPrettifier()


###############################################################################################################
### CLASS MarshMaker - place Marsh Terrain on the map
###############################################################################################################
### Convert grass or tundra flatlands to marsh
###   if they are within a hot range near the equator (giving hot jungle swamps)
###   or within a cold range near the polar circle (givng colder fens).
###############################################################################################################
# bModHasMarsh = initialize( iGrassChance=5, iTaigaChance=10, tMarshHotRange=(0,18), tMarshColdRange=(45,63) )
# convertTerrain( tAreaRange=None, areaID=None )
# iArid = getAridity()
# normalizeMarshes()
# --- private ---
# convertTerrainPlot( plot )
# buildMarshlands( plot, eTerrain )
###############################################################################################################
class MarshMaker:

	# class variables
	bModHasMarsh      = None
	iMarshHotBottom   = 0
	iMarshHotTop      = 18
	iMarshColdBottom  = 45
	iMarshColdTop     = 63
	chGrass           = 5
	chTaiga          = 12
	cntGrass          = 0
	cntTaiga         = 0

	# Latitudes in ranges must be between 0 .. 90
	def initialize( self, iGrassChance=5, iTaigaChance=10, tMarshHotRange=(0,18), tMarshColdRange=(45,63) ):
		print "[MST] ===== MarshMaker:initialize( %r, %r, %r, %r )" % (iGrassChance, iTaigaChance, tMarshHotRange, tMarshColdRange)
		if self.bModHasMarsh != None:
			print "[MST] was already initialized! - use new parameter values"

		self.chGrass  = iGrassChance
		self.chTaiga = iTaigaChance

		# ranges 0..90
		self.iMarshHotBottom   = int( tMarshHotRange[0] )
		self.iMarshHotBottom   = min( self.iMarshHotBottom, 90 )
		self.iMarshHotBottom   = max( self.iMarshHotBottom, 0 )

		self.iMarshHotTop      = tMarshHotRange[1]
		self.iMarshHotTop     += int( 90 * gc.getClimateInfo(map.getClimate()).getSnowLatitudeChange() ) #must keep getSnow, comes from API
		self.iMarshHotTop      = min( self.iMarshHotTop, 90 )
		self.iMarshHotTop      = max( self.iMarshHotTop, 0 )

		self.iMarshColdBottom  = tMarshColdRange[0]
		self.iMarshColdBottom += int( 90 * gc.getClimateInfo(map.getClimate()).getDesertBottomLatitudeChange() )
		self.iMarshColdBottom  = min( self.iMarshColdBottom, 90 )
		self.iMarshColdBottom  = max( self.iMarshColdBottom, 0 )

		self.iMarshColdTop     = tMarshColdRange[1]
		self.iMarshColdTop    += int( 90 * gc.getClimateInfo(map.getClimate()).getDesertTopLatitudeChange() )
		self.iMarshColdTop     = min( self.iMarshColdTop, 90 )
		self.iMarshColdTop     = max( self.iMarshColdTop, 0 )
		sprint = "[MST] Marsh ranges for %s - Hot Swamp: [%r,%r], Cold Fen: [%r,%r] \n" % (sClimateType,self.iMarshHotBottom,self.iMarshHotTop,self.iMarshColdBottom,self.iMarshColdTop)

		# adjust marsh chances
		if sClimateType=="CLIMATE_TROPICAL":
			self.chGrass  += 1
			self.chTaiga += 3
		elif sClimateType=="CLIMATE_ARID":
			self.chGrass  -= 1
			self.chTaiga -= 3
		elif sClimateType=="CLIMATE_ROCKY":
			self.chGrass  -= 1
			self.chTaiga -= 1
		elif sClimateType=="CLIMATE_COLD":
			self.chGrass  -= 1
			self.chTaiga += 2
		sprint += "[MST] Base chances to change: %s - Grass->Marsh %i%s, Taiga->Marsh %i%s \n" % (sClimateType, self.chGrass, "%%", self.chTaiga, "%%")

		# test if Mod supports marsh
		if bPfall:
			self.bModHasMarsh = False
		else:
			self.bModHasMarsh = (etMarsh >= 0) and (etMarsh != etGrass)
		sprint += "[MST] Mod supports Marsh: %r \n" % (self.bModHasMarsh)
		print sprint
		return self.bModHasMarsh

	# add marsh-terrain to given region or whole map
	# tAreaRange is a 3-tuple (x,y,iRange) describing the area around x,y up to iRange distance
	def convertTerrain( self, tAreaRange=None, areaID=None ):
		print "[MST] ===== MarshMaker:convertTerrain()"
		if bPfall or bMars:
			print "[MST] No Marshes on Mars or in Planetfall"
			return
		if not self.bModHasMarsh:
			print "[MST] No Marshes in this Mod"
			return

		if tAreaRange == None:
			minX = 0
			maxX = map.getGridWidth() - 1
			minY = 0
			maxY = map.getGridHeight() - 1
		else:
			minX = tAreaRange[0] - tAreaRange[2]
			maxX = tAreaRange[0] + tAreaRange[2]
			minY = tAreaRange[1] - tAreaRange[2]
			maxY = tAreaRange[1] + tAreaRange[2]

		self.cntTaiga = 0
		self.cntGrass  = 0
		for x in range( minX, maxX+1 ) :
			for y in range( minY, maxY+1 ):
				plot = plotXY( x, y, 0, 0 )
				if not plot.isNone():
					if (areaID == None) or (areaID == plot.getArea()):
						self.convertTerrainPlot( plot )
		print "[MST] %i plots converted to Marsh: %i from Grass, %i from Taiga" % (self.cntGrass+self.cntTaiga,self.cntGrass,self.cntTaiga)

	# return aridity -3 .. 3
	def getAridity( self ):
		print "[MST] ===== MarshMaker:getAridity()"
		arid = 0
		if sClimateType=="CLIMATE_ARID":
			arid += 2
		elif sClimateType=="CLIMATE_COLD":
			arid += 1
		elif sClimateType=="CLIMATE_ROCKY":
			arid += 1
		elif sClimateType=="CLIMATE_TROPICAL":
			arid += -2
		if sSeaType=="SEALEVEL_LOW":
			arid += 1
		elif sSeaType=="SEALEVEL_HIGH":
			arid += -1
		return arid

	# make sure marshes are only on flatlands
	def normalizeMarshes( self ):
		print "[MST] ===== MarshMaker:normalizeMarsh()"
		if bPfall or (not self.bModHasMarsh): return
		pcnt = 0
		for inx in range( map.numPlots() ):
			plot = map.plotByIndex( inx )
			if plot.isHills():
				if plot.getTerrainType() == etMarsh:
					plot.setTerrainType(etGrass, True, True)
					pcnt += 1
		if pcnt > 0: print "[MST] %i marshy hills converted to grasslands" % (pcnt)

	###############
	### Helpers ###
	###############

	# assign chances for conversion to plot and choose
	def convertTerrainPlot( self, plot ):
#		print "[MST] ======== MarshMaker:convertTerrainPlot()"
		if plot.isFlatlands():
			iLat = abs( plot.getLatitude() )
			eTerrain = plot.getTerrainType()
			if self.iMarshHotBottom<=iLat and iLat<=self.iMarshHotTop:
				# tundra near equator is always converted
				if eTerrain==etTaiga:
					self.buildMarshlands( plot, eTerrain )
					return
			if (self.iMarshHotBottom<=iLat and iLat<=self.iMarshHotTop) or (self.iMarshColdBottom<=iLat and iLat<=self.iMarshColdTop):
				iWet = 0.3
				if plot.isFreshWater(): iWet += 1.2
				if plot.isCoastalLand(): iWet += 0.3
				if eTerrain==etTaiga:
					if choose( int(iWet*self.chTaiga), True, False ):
						self.buildMarshlands( plot, eTerrain )
				elif eTerrain==etGrass:
					if choose( int(iWet*self.chGrass), True, False ):
						self.buildMarshlands( plot, eTerrain )
				elif eTerrain==etMarsh:
					self.buildMarshlands( plot, eTerrain )		# give extra chance to convert neighbor

	# put marsh on map and try for a neighbor
	def buildMarshlands( self, plot, eTerrain ):
#		print "[MST] ======== MarshMaker:buildMarshlands()"
		sprint = ""
		if eTerrain==etMarsh:									# if already marsh, check if we want to convert neighbor
			if choose( 80, True, False): return
		else:
			plot.setTerrainType( etMarsh, True, True )
			if eTerrain==etTaiga:
				self.cntTaiga += 1
			else:
				self.cntGrass += 1
			sprint += "[MST] Marsh created @ %i,%i \n" % (plot.getX(),plot.getY())

		# add one or two more marshes to keep the plot from getting lonely and strange
		x = plot.getX()
		y = plot.getY()
		pList = []
		for eCard in range( CardinalDirectionTypes.NUM_CARDINALDIRECTION_TYPES ):
			p = plotCardinalDirection( x, y, CardinalDirectionTypes(eCard) )
			if not p.isNone():
				if p.isFlatlands():
					eTerrain = p.getTerrainType()
					if (eTerrain==etGrass) or (eTerrain==etTaiga):
						pList.append( p )
						# plots with freshwater get two chances
						if plot.isFreshWater():
							pList.append( p )

		if len(pList)>0:
			randomList.shuffle( pList )
			if etTaiga==pList[0].getTerrainType():
				self.cntTaiga += 1
			else:
				self.cntGrass += 1
			pList[0].setTerrainType( etMarsh, True, True )
			sprint += "[MST] - More Marsh created @ %i,%i \n" % (pList[0].getX(),pList[0].getY())
			if (len(pList)>2) and choose( 25, True, False ):
				if pList[0] <> pList[1]:
					iLat = abs( pList[1].getLatitude() )
					if (self.iMarshHotBottom<=iLat and iLat<=self.iMarshHotTop) or (self.iMarshColdBottom<=iLat and iLat<=self.iMarshColdTop):
						pList[1].setTerrainType( etMarsh, True, True )
						sprint += "[MST] - More Marsh created @ %i,%i \n" % (pList[1].getX(),pList[1].getY())
#		print sprint

##############################################################################################################
### CLASS MarshMaker END
##############################################################################################################
marshMaker = MarshMaker()


###############################################################################################################
### CLASS MapRegions - special regions you can place on your map
###############################################################################################################
### - The Big Bog (big, small, with or without lake )
### - The Big Dent (single, double and sideways)
### - Elemental Quarter (FFH only)
### Create special features on the map. Use after generateTerrainTypes() and before addRivers()
###############################################################################################################
# initialize( regDist=15 )
# buildLostIsle( chance=33, minDist=7, bAliens=False )
# namePlot = theLostIsle( pCenterPlot, pList, bAliens )
# buildBigBogs( iBogs=None )
# namePlot = theBigBog( pCenterPlot, bBigBog=True, bBogLake=True )
# buildBigDents( iDents=None )
# namePlot = theBigDent( pCenterPlot, bSideways=None, chAccess=66 )
# adjustBigDentsTemplate( bRandom )
# buildElementalQuarter( self, chEQ=66 )
# theElementalQuarter( pCenterPlot, temp )
# addRegionExtras()
# --- private ---
# template = rotateTemplate( tempDict, steps )
# addLostIsleExtras()
# addBigBogExtras()
# addBigDentExtras()
# addElementalQuarterExtras()
# bValid = regionCheck( plot )
# deleteNonBogPlots( plotList )
# deleteNonDentPlots( plotList )
# log = changeBogTerrain( plot, temp )
# tileList = createLostIsle( minDist, bAliens )
# tileList = stampLostIsle( template, center )
# stampElementalQuarter()
###############################################################################################################
class MapRegions:

	# class variables
	noSigns = False
	regionNames = []
	regionList = []
	regionDist = 15
	# 1 probably lake, 2 marshy and flat, 3 probably marsh 4 probably grass 5 probably hills/peaks - no snow/desert
	bigBogTemplate   = {	0: [0,0,0,4,5,5,4,0,0,0,0],
								1: [0,0,5,4,4,4,4,4,5,0,0],
								2: [0,5,4,4,3,3,3,3,4,5,0],
								3: [0,4,3,2,2,2,2,2,3,4,0],
								4: [5,4,3,2,1,1,2,2,3,4,5],
								5: [5,4,3,2,1,1,2,2,3,4,5],
								6: [0,4,3,2,2,2,2,2,3,4,0],
								7: [0,5,4,4,3,3,3,4,4,5,0],
								8: [0,0,5,4,3,3,4,4,5,0,0],
								9: [0,0,0,5,4,4,5,0,0,0,0]
								}
	# 1 probably lake, 2 marshy and flat, 3 probably marsh 4 probably grass 5 probably hills/peaks - no snow/desert
	smallBogTemplate = {	0: [0,0,5,5,4,0,0],
								1: [0,5,4,3,4,5,0],
								2: [4,3,3,2,3,4,4],
								3: [4,3,2,1,2,4,5],
								4: [5,4,2,1,2,4,5],
								5: [4,3,2,2,2,4,5],
								6: [4,3,3,2,3,3,4],
								7: [0,5,4,3,4,5,0],
								8: [0,0,4,5,4,0,0]
								}
	bogList = []
	bogLakes = []
	bogRivers = None
	# 1 possibly Volcano, 2 probably Peaks, 3 probably Peaks/Hills, 4 probably Hills
	bigDentTemplate  = {	0: [0,0,0,0,4,4,4,4,3,4,0,0,0,0],
								1: [0,0,4,4,4,3,3,3,3,3,4,4,0,0],
								2: [0,4,4,3,3,2,2,3,2,3,3,3,4,0],
								3: [0,4,3,2,4,2,2,2,2,2,2,3,4,0],
								4: [4,3,2,2,2,1,1,4,1,2,3,2,3,4],
								5: [4,3,2,2,1,1,2,2,1,1,4,2,3,4],
								6: [0,4,3,2,2,2,4,2,2,2,2,3,4,0],
								7: [0,4,4,3,3,2,2,2,2,3,3,4,4,0],
								8: [0,0,4,4,4,3,3,3,3,3,4,4,0,0],
								9: [0,0,0,0,4,4,4,4,4,4,0,0,0,0]
								}
	dentList = []
	dentVolcanos = []
	dentRivers = None
	dentTemplate = {}
	# F,f Fire - E,e Earth - A,a Air - W,w Water - D,d Desert - P,p Plains - G,g Grass - m Marsh
	eqTemplate = {	5: ['w','w','w','G','e','e'],
						4: ['w','W','m','g','E','e'],
						3: ['w','w','m','P','D','P'],
						2: ['g','g','g','p','D','d'],
						1: ['a','A','d','d','F','f'],
						0: ['a','a','p','d','f','f']
						}
	eqList = []
	eqVolcanos = []
	eqRivers = None
	# Lost Isle - 3 Peak, 2 Hills, 1 Land, 0 Ocean
	lostIsleTemplate = { 4: [0, 0, 3, 0, 0],
								3: [0, 1, 2, 3, 0],
								2: [0, 2, 0, 2, 3],
								1: [3, 2, 1, 1, 2],
								0: [0, 3, 3, 3, 0]
								}
	lostIsleList = []


	# initialize class variables
	def initialize( self, regDist=15, noSigns=False ):
		print "[MST] ===== MapRegions:initialize( regDist=%r, noSigns=%r )" % ( regDist, noSigns )
		# class
		self.noSigns = noSigns
		self.regionNames = []
		self.regionList = []
		self.regionDist = regDist + map.getWorldSize()
		# bigbog
		self.bogList = []
		self.bogLakes = []
		self.bogRivers = None
		# bigdent
		self.bigDentTemplate  = {	0: [0,0,0,0,4,4,4,4,3,4,0,0,0,0],
											1: [0,0,4,4,4,3,3,3,3,3,4,4,0,0],
											2: [0,4,4,3,3,2,2,3,2,3,3,3,4,0],
											3: [0,4,3,2,4,2,2,2,2,2,2,3,4,0],
											4: [4,3,2,2,2,1,1,4,1,2,3,2,3,4],
											5: [4,3,2,2,1,1,2,2,1,1,4,2,3,4],
											6: [0,4,3,2,2,2,4,2,2,2,2,3,4,0],
											7: [0,4,4,3,3,2,2,2,2,3,3,4,4,0],
											8: [0,0,4,4,4,3,3,3,3,3,4,4,0,0],
											9: [0,0,0,0,4,4,4,4,4,4,0,0,0,0]
											}
		self.dentList = []
		self.dentVolcanos = []
		self.dentRivers = None
		self.dentTemplate = {}
		# elementalquarter
		self.eqList = []
		self.eqVolcanos = []
		self.eqRivers = None

	# build formerly populated island
	def buildLostIsle( self, chance=33, minDist=7, bAliens=False ):
		if bPfall: bAliens = True
		print "[MST] ===== MapRegions:buildLostIsle(%r,%r,%r)" % (chance, minDist, bAliens)

		if choose( chance, False, True ):
			print "[MST] No Lost Isle choosen"
			return

		# get continents and islands
		map.recalculateAreas()
		areaList = CvMapGeneratorUtil.getAreas()
		isleList = []

		# make Lost Isle
		islePlotCoordList = self.createLostIsle( minDist, bAliens )
		islePlotCoordList.sort()
		islePlotCoordList.reverse()
		if len(islePlotCoordList) == 0:
			print "[MST] Unable to create Lost Isle"
			return

		# build Lost Isle
		x,y = islePlotCoordList[0]		# should be the plot to the upper right
		namePlot = self.theLostIsle( GetPlot(x,y), islePlotCoordList, bAliens )
		mapSetSign( namePlot, "The Lost Isle", self.noSigns )
		self.regionNames.append( ('LostIsle', "The Lost Isle", namePlot) )
		printList( islePlotCoordList, "islePlotCoordList:", rows = 1, prefix = "[MST] " )
		print "[MST] Lost Isle built @ (%r,%r)" % (x,y)

	# register where and how the 'Lost Isle' should be built
	def theLostIsle( self, pCenterPlot, pList, bAliens ):
		print "[MST] ===== MapRegions:theLostIsle()"

		# get coordinates
		x0 = pCenterPlot.getX()
		y0 = pCenterPlot.getY()
		# register
		self.regionList.append( [x0, y0] )
		self.lostIsleList.append( [x0, y0, pList, bAliens] )
		return pCenterPlot

	#----------------------------------------------------------------------------
	#        dx-4 dx  dx+5
	#         !   !    !
	#        ............  		. no change
	# dy+4   .....hh.....  		h chance for new hills or peak , no snow or desert
	# dy+3   ...hggggh...  		g probably grass - probably flat
	# dy+2   ..hggmmggh..  		m probably marsh - flat
	#  .     ..gmmmmmmg..     	o probably lake
	# dy     .hgmmoommgh.
	#  .     ..gmmmmmmg..  		there may be a single peak somewhere
	# dy-2   ..hggmmggh..
	# dy-3   ...hggggh...
	# dy-4   .....hh.....
	#        ............
	#         !   !    !
	#        dx-4 dx  dx+5
	#----------------------------------------------------------------------------
	#  - if iBogs>0: try build The BigBog, on two biggest continents
	#  - if iBogs>builtBogs: try build 1st smallBog with lake, on four biggest continents
	#  - if iBogs>builtBogs: try build 2nd smallBog without lake, on four biggest continents
	def buildBigBogs( self, iBogs=3 ):
		print "[MST] ===== MapRegions:buildBigBogs()"

		# no bogs on Mars
		if bMars: return

		# init marshMaker if neccessary
		if marshMaker.bModHasMarsh == None: marshMaker.initialize()

		nBog = 0
		chBigBog = 75
		chSmallBog = 66
		bLake = False
		# one BigBog
		if choose( chBigBog, True, False ) and (iBogs > nBog):
			# get two biggest continents
			continents = getBigAreas( 2, False )					# [ (iNumPlots, iAreaID, plotList), ... ]
			for inx in range( len( continents ) ):
				self.deleteNonBogPlots( continents[inx][2] )
				continents[inx][0] = len( continents[inx][2] )
			sprint = ""
			for area in continents:	sprint += "[MST] BigBogAreas: ID:%7i,  Plots:%4i \n" % ( area[1], area[0] )
			print sprint
			# get valid plots
			validPlots = [ p for num,id,pList in continents
							 for p in pList
							 if self.regionCheck( p ) and self.wrapCheck( p ) ]

			# build big bog
			if len( validPlots ) > 0:
				plot = chooseListElement( validPlots )
				namePlot = self.theBigBog( plot, True )									# do the big bog
				nBog += 1
				# set landmark
				if plot.isWater():
					mapSetSign( namePlot, "Big Bog Lake", self.noSigns )
				else:
					mapSetSign( namePlot, "The Big Bog", self.noSigns )
				self.regionNames.append( ('Bog', "Big Bog", namePlot) )
			else:
				print "[MST] No Big Bog"

		# one SmallBog with Lake
		if choose( chSmallBog, True, False ) and (iBogs > nBog):
			# get four biggest continents
			continents = getBigAreas( 4, False )
			for inx in range( len( continents ) ):
				self.deleteNonBogPlots( continents[inx][2] )
				continents[inx][0] = len( continents[inx][2] )
			sprint = ""
			for area in continents:	sprint += "[MST] SmallBogAreas: ID:%7i,  Plots:%4i \n" % ( area[1], area[0] )
			print sprint
			# get valid plots
			validPlots = [ p for num,id,pList in continents
							 for p in pList
							 if self.regionCheck( p ) and self.wrapCheck( p ) ]
			# build small bog
			if len( validPlots ) > 0:
				plot = chooseListElement( validPlots )
				namePlot = self.theBigBog( plot, False, True )							# do the small bog with lake
				nBog += 1
				# set landmark
				mapSetSign( namePlot, "Darkwater Lake", self.noSigns )
				self.regionNames.append( ('Bog', "Darkwater", namePlot) )
				if map.getWorldSize() < 2: chSmallBog = chSmallBog / 2
			else:
				print "[MST] No Small Bog with Lake"

		# one SmallBog without Lake
		if choose( chSmallBog, True, False ) and (iBogs > nBog):
			# get four biggest continents
			continents = getBigAreas( 4, False )
			for inx in range( len( continents ) ):
				self.deleteNonBogPlots( continents[inx][2] )
				continents[inx][0] = len( continents[inx][2] )
			sprint = ""
			for area in continents:	sprint += "[MST] SmallBogAreas: ID:%7i,  Plots:%4i \n" % ( area[1], area[0] )
			print sprint
			# get valid plots
			validPlots = [ p for num,id,pList in continents
							 for p in pList
							 if self.regionCheck( p ) and self.wrapCheck( p ) ]
			# build small bog
			if len( validPlots ) > 0:
				plot = chooseListElement( validPlots )
				namePlot = self.theBigBog( plot, False, False )						# do the small bog without lake
				nBog += 1
				# set landmark
				if bMarsh:
					if namePlot.isFlatlands():
						if namePlot.getTerrainType() != etMarsh:
							namePlot.setTerrainType( etMarsh, True, True )
				mapSetSign( namePlot, "Darkwater Moor", self.noSigns )
				self.regionNames.append( ('Bog', "Darkwater", namePlot) )
			else:
				print "[MST] No Small Bog without Lake"
		print "[MST] %i bogs built: %r" % ( nBog, self.bogList )
#		print "[MST] Regions: %r" % ( self.regionList )

	# Builds boglands with a lake surrounded by hills and outflowing rivers
	# Center needs to be on land and have marshy latitude
	def theBigBog( self, pCenterPlot, bBigBog=True, bBogLake=True ):
#		print "[MST] ======== MapRegions:theBigBog()"
		if pCenterPlot==None: return None

		# get template
		if bBigBog:
			template = self.bigBogTemplate.copy()
			if map.getWorldSize() < 4:
				del template[5]
		else:
			template = self.smallBogTemplate.copy()
			if (map.getWorldSize() < 4) and choose(80, True, False):
				del template[5]
			if (map.getWorldSize() < 2) and choose(80, True, False):
				del template[3]
		rot = chooseNumber( 4 )
		template = self.rotateTemplate( template, rot )
		printDict( template, "rotated %i" % (rot), prefix="[MST] " )
		print "[MST] Template rotated %i degrees" % (rot*90)

		# get region size
		x0   = pCenterPlot.getX()
		minX = x0 + 1 - ( len( template[0] ) / 2 ) + ( len( template[0] ) % 2 )
		maxX = minX + len( template[0] ) - 1
		k = len( template.keys() )
		y0   = pCenterPlot.getY()
		minY = y0 + 1 - ( k / 2 ) + ( k % 2 )
		maxY = minY + k - 1

		# handle namePlot
		namePlot = None			#
		for dy in range( minY, maxY + 1 ):
			for dx in range( minX, maxX + 1 ):
				if template[dy-minY][dx-minX] == 1:
					namePlot = map.plot( dx, dy )
					break
		if namePlot == None:
			namePlot = GetPlot( minX + (maxX - minX) / 2, minY - 1 + (maxY - minY) / 2 )
		x0, y0 = coordByPlot( namePlot )

		# register
		if bBigBog: bBogLake = True									# Big Bogs can always have a lake
		self.regionList.append( [x0, y0] )
		self.bogList.append( [x0, y0, bBigBog, bBogLake] )
		print "[MST] Building %s bog @ %3i,%2i %s \n" % ( iif(bBigBog,"big", "small"), x0, y0, "with"+iif(bBogLake,"","out")+" Lake" )

		# pass 1 - change plots
		sprint = ""
		sprint += "[MST] pass 1 - change plots \n"
		chFlatHill  = 80				# chance to flatten hills
		chPeakHill  = 80				# chance to flatten peaks
		chLake      = 90				# chance to make lake
		for dx in range( minX, maxX + 1 ):
			for dy in range( minY, maxY + 1 ):
				temp = template[dy-minY][dx-minX]
				if temp==0: continue																# ignore
				plot = plotXY( dx, dy, 0, 0 )
				if plot.isNone(): continue														# no plot -> ignore
				if temp>0:
					if plot.isLake(): continue													# lake stays
					elif temp==5:
						if plot.isFlatlands():
							if choose( chPeakHill, True, False ):
								plot.setPlotType( PlotTypes.PLOT_PEAK, True, True )	# Flat -> Peak
							else:
								plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )	# Flat -> Hills
						elif plot.isWater():
							if choose( chPeakHill/2, True, False ):
								plot.setPlotType( PlotTypes.PLOT_PEAK, True, True )	# Flat -> Peak
							else:
								plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )	# Flat -> Hills
					elif plot.isWater():
						plot.setPlotType( PlotTypes.PLOT_LAND, True, True )			# Ocean -> Land
					elif plot.isPeak():															# Peak -> Land
						iChange = chFlatHill
						if temp==4:																	# 10%: Peak -> Land
							iChange = 100 - iChange
						if choose( iChange, True, False):									# 90%: Peak -> Land
							plot.setPlotType( PlotTypes.PLOT_LAND, True, True )
						else:
							plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
					elif plot.isHills():
						iChange = chFlatHill
						if temp==4:																	# 10%: Hills -> Land
							iChange = 100 - iChange
						if choose( iChange, True, False):									# 90%: Hills -> Land
							plot.setPlotType( PlotTypes.PLOT_LAND, True, True )
					if temp==1:
						if choose( chLake, True, False ):
							plot.setPlotType( PlotTypes.PLOT_OCEAN, True, True )		# make lake

		# handle bog lake
		if bBogLake:
			namePlot.setPlotType( PlotTypes.PLOT_OCEAN, True, True )
		else:
			if namePlot.isWater():
				namePlot.setPlotType( PlotTypes.PLOT_LAND, True, True )

		# pass 2 - change terrain
		sprint += "[MST] pass 2 - change terrain \n"
		for dx in range( minX, maxX + 1 ):
			for dy in range( minY, maxY + 1 ):
				temp = template[dy-minY][dx-minX]
				if temp==0: continue															# ignore
				plot = plotXY( dx, dy, 0, 0 )
				if plot.isNone(): continue													# no plot -> ignore
				if plot.isWater(): continue												# ignore lakes
				if plot.isPeak(): continue													# ignore peaks
				log = self.changeBogTerrain( plot, temp )								# change terrain to bog
				# sprint += log
				if not bPfall:
					if plot.isHills() and plot.getTerrainType()==etMarsh:			# no marsh on hills
						plot.setTerrainType( etGrass, True, True )
				else: pass																		# PlanetFall has no such restriction

		# pass 3 - change surrounding desert to plains (arid to moist)
		sprint += "[MST] pass 3 - change surrounding desert/snow \n"
		for dx in range( minX-1, maxX + 2 ):
			for dy in range( minY-1, maxY + 2 ):
				if ( (dy==minY-1) or (dy==maxY+1) or (dx==minX-1) or (dx==maxX+1) ):
					plot = plotXY( dx, dy, 0, 0 )
					if not plot.isNone():
						if bPfall:
							if plot.getTerrainType()==etFlatArid:						# no arid bog neighbor
								plot.setTerrainType( etFlatMoist, True, True )
							elif plot.getTerrainType()==etRockyArid:
								plot.setTerrainType( etRockyMoist, True, True )
						else:
							if plot.getTerrainType()==etTundra:								# no snow bog neighbor
								plot.setTerrainType( etTaiga, True, True )
							elif plot.getTerrainType()==etDesert:						# no desert bog neighbor
								plot.setTerrainType( etPlains, True, True )

		# pass 4 - build river(s) ending in water
		sprint += "[MST] pass 4 - build river(s) ending in water \n"
		print sprint
		sprint = ""
		rStart = []
		# start rivers
		map.recalculateAreas()
		if namePlot.isWater:
			# bog-lake found: start river(s) here
			id = map.plot( x0, y0 ).getArea()
			riverMaker.buildRiversFromLake( id, 100, iif(bBigBog, 2, 1), 1 )
		else:
			# no bog-lake found: start rivers from rim
			rivStart = riverMaker.rimRivers( x0, y0, [5,4,3] )		# [ bogDir, riverPlot, eCard ]
			lastDir = []
			for i in [0,1]:
				if len(rivStart) == 0: break
				inx = chooseListIndex( rivStart )
				bogDir, rPlot, eCard = rivStart[inx]
				while (bogDir in lastDir) and ( len(rivStart) > 0 ):
					bogDir, rPlot, eCard = chooseListPop( rivStart )
				if bogDir in lastDir: break
				if lastDir == []:
					lastDir.append( bogDir )
					lastDir.append( addDirection(bogDir, 1) )
					lastDir.append( addDirection(bogDir,-1) )
				# found one - make river
				sprint = ""
				sprint += "[MST] Lake: None - River-Start @ %i,%i --> %5s - %s \n" % (rPlot.getX(), rPlot.getY(), cardinalName(eCard), "Normal Flow" )
				rList = []
				riverMaker.buildRiver( rPlot, True, eCard, riverList=rList )
				sprint += riverMaker.outRiverList( rList, "[MST]" )
				print sprint
		return namePlot

	#------------------------------------------------------------------------
	#                                        dx
	#                                         !
	#             dx                      ...........
	#              !              dy+5+s  .....h.....    . no change
	#        .......|......       dy+4+s  ...hhHhh...    h hilly
	# dy+4   .....hh|h.....       dy+3+s  ..hhH^Hhh..    H hills or peaks
	# dy+3   ...hhHH|Hhh...       dy+2+s  ..hH^^^Hh..    ^ mountainous
	# dy+2   ..hhHH^|HHhh..       dy+1+s  .hHH^M^HHh.    M Mountains probably
	# dy+1   ..hH^^^|^^Hh..               -----------
	# dy     .hH^^MM|M^^Hh.       dy      .hH^^M^^Hh.    s size adjustment
	# dy-1   ..hH^^^|^^Hh..       dy-1    .hHH^M^HHh.      0 duel, tiny, small
	# dy-2   ..hhHH^|HHhh..       dy-2    ..hH^^^Hh..      1 standard
	# dy-3   ...hhHH|Hhh...       dy-3    ..hhH^Hhh..      2 large
	# dy-4   .....hh|h.....       dy-4    ...hhHhh...      3 huge
	#        .......|......       dy-5    .....h.....      4 giant
	#         !    !     !                ...........      5 gigantic
	#       dx-5  dx  dx+5+s               !   !   !
	#                                    dx-4 dx dx+4
	#
	#------------------------------------------------------------------------

	# build several BigDents
	#	- if iDents>0: try build 1st bigDent, not sideways, maybe as doubleDent
	#  - if iDents>builtDents: if mapsize>tiny: try build 2nd bigDent, maybe sideways
	#  - if iDents>builtDents: if mapsize>standard: try build 3rd bigDent, maybe sideways
	#  - except for doubleDent: don't use same continent twice
	def buildBigDents( self, iDents=3 ):
		print "[MST] ===== MapRegions:buildBigBDents()"

		# Names for Mountain Ranges
		dentNames = [
							{
								'Volcano': "Big Brothers Doom",
								'Peak':    "The Big Brother",
								'Flat':    "Watchers Retreat",
								'Water':   "Watchers Pool",
								'Hills':   "Big Brother Range"
							},
							{
								'Volcano': "Hole of the World",
								'Peak':    "The Big Dent",
								'Flat':    "Hammers Rest",
								'Water':   "Hole of the World",
								'Hills':   "Big Dent Highlands"
							},
							{
								'Volcano': "Roaring Spike",
								'Peak':    "The Great Spine",
								'Flat':    "Lost Valley",
								'Water':   "Forgotten Hollow",
								'Hills':   "Great Spinal Mountains"
							},
							{
								'Volcano': "Abyss Portal",
								'Peak':    "Celestial Throne",
								'Flat':    "Paradise Meadow",
								'Water':   "Divine Bath",
								'Hills':   "Celestial Belt"
							},
							{
								'Volcano': "Demons Breath",
								'Peak':    "Roof of the World",
								'Flat':    "Banshies Playground",
								'Water':   "Devils Pool",
								'Hills':   "Howling Barrier"
							},
							{
								'Volcano': "Witches Cauldron",
								'Peak':    "Warlocks Hat",
								'Flat':    "Fairies Glen",
								'Water':   "Satyrs Lake",
								'Hills':   "Wizard Mountains"
							}
						]

		if bPfall:
			dentBoni =	{
								'Flat':		[ ebSilver, ebGrenadeFruits, ebRareDnaMoist, ebRareDnaRainy, ebFungalGin, ebThorium ],
								'Hills':		[ ebSilver, ebGrenadeFruits, None, ebFungicide, ebGold, ebThorium ],
								'Terrain':	[ etFlatArid, etFlatMoist, etFlatMoist, etFlatRainy, etFlatMoist, etFlatPolar ]
							}
		else:
			dentBoni =	{
								'Flat':		[ ebSilver, ebFur, ebDeer, ebMarble, ebCow, ebHorse ],
								'Hills':		[ ebSilver, ebMarble, ebGold, ebGems, ebSheep, None ],
								'Terrain':	[ etTundra, etTaiga, etTaiga, etMarsh, etGrass, etGrass ]
							}

		# start building
		nDent = 0
		chDent = 75
		chDoubleDent = 33
		bDouble = False
		# First BigDent
		if choose( chDent, True, False ) and (iDents > nDent):
			# get two biggest continents
			continents = getBigAreas( 2, False )
			for inx in range( len( continents ) ):
				self.deleteNonDentPlots( continents[inx][2] )
				continents[inx][0] = len( continents[inx][2] )
			sprint = ""
			for area in continents:	sprint += "[MST] 1st BigDentAreas: ID:%7i,  Plots:%4i \n" % ( area[1], area[0] )
			print sprint
			# get valid plots
			validPlots = [ p for num,id,pList in continents
							 for p in pList
							 if self.regionCheck( p ) and self.wrapCheck( p ) ]
			# build first dent
			if len( validPlots ) > 0:
				plot = chooseListElement( validPlots )
				self.adjustBigDentsTemplate()
				namePlot = self.theBigDent( plot, False )											# do the first dent
				nDent += 1
				# get landmark bonus
				pos = chooseNumber(5)
				eTerr = dentBoni['Terrain'][pos]
				eFlat = dentBoni['Flat'][pos]
				eHills = dentBoni['Hills'][pos]
				# set landmark
				dentDict = chooseListPop( dentNames )
				dentDict['Plot'] = namePlot
				eForest = -1
				if not bPfall:
					if eTerr in [etMarsh, etGrass]:
						eForest = chooseMore( (25,efJungle), (66,efForest), (100,-1) )
					if (eForest == efJungle) and (evalLatitude(namePlot) > 60):
						eForest = efForest
				dentDict['Flat'] = [ dentDict['Flat'], eTerr, eForest, eFlat ]
				if bFFH and (eHills == ebSilver):
					if choose(33, True, False):
						eHills = ebMithril
				dentDict['Hills'] = [ dentDict['Hills'], eHills ]
				mapSetSign( namePlot, dentDict['Hills'][0], self.noSigns )
				self.regionNames.append( ('Dent', dentDict) )
				# check for double dent
				if (map.getWorldSize() > 2) and (iDents > 1):
					if choose( chDoubleDent, True, False ):
						rad = 12 + chooseNumber( 6 )
						x0 = plot.getX()
						y0 = plot.getY()
						plotList = []
						for dx in range(-rad, rad+1):
							for dy in range(-rad, rad+1):
								if abs(dy) > (rad/3): continue
								pl = plotXY( x0, y0, dx, dy )
								if pl.isNone(): continue
								dist = rad + iif(dy in [-1,0,1],3,0) + iif(dy in [-2,-1,0,1,2],2,0) + iif(dy in [-3,-2,-1,0,1,2,3],1,0)
								if plotDistance( x0, y0, x0+dx, y0+dy ) == dist:
									plotList.append( pl )
						self.deleteNonDentPlots( plotList )
						if len( plotList ) > 0:
							pl = chooseListElement( plotList )
							self.adjustBigDentsTemplate( True )
							bSide = choose(25, True, False)
							namePlot = self.theBigDent( pl, bSide )							# make double dent
							nDent += 1
							bDouble = True
							# get landmark bonus
							pos = chooseNumber(5)
							eTerr = dentBoni['Terrain'][pos]
							eFlat = dentBoni['Flat'][pos]
							eHills = dentBoni['Hills'][pos]
							# set landmark
							dentDict = chooseListPop( dentNames )
							dentDict['Plot'] = namePlot
							eForest = -1
							if not bPfall:
								if eTerr in [etMarsh, etGrass]:
									eForest = chooseMore( (25,efJungle), (66,efForest), (100,-1) )
								if (eForest == efJungle) and (evalLatitude(namePlot) > 60):
									eForest = efForest
								if (eForest == efJungle) and (evalLatitude(namePlot) < 45):
									if choose(33, True, False):
										eFlat = ebBanana
							dentDict['Flat'] = [ dentDict['Flat'], eTerr, eForest, eFlat ]
							dentDict['Hills'] = [ dentDict['Hills'], eHills ]
							mapSetSign( namePlot, dentDict['Hills'][0], self.noSigns )
							self.regionNames.append( ('Dent', dentDict) )
						else: sprint += " No room for DoubleDent \n"

		# Later BigDents
		minMap = 2
		while (map.getWorldSize() > minMap) and (iDents > nDent):
			if choose( chDent/(minMap-1), True, False ):
				# get two biggest continents
				noAreas = []
				for dx,dy,dummy in self.dentList: noAreas.append( plotXY(dx,dy,0,0) )
				continents = getBigAreas( 3, False, noAreas )
				for inx in range( len( continents ) ):
					self.deleteNonDentPlots( continents[inx][2] )
					continents[inx][0] = len( continents[inx][2] )
				sprint = ""
				for area in continents:	sprint += "[MST] Next BigDentAreas: ID:%7i,  Plots:%4i \n" % ( area[1], area[0] )
				print sprint
				# get valid plots
				validPlots = [ p for num,id,pList in continents
									  for p in pList
									  if self.regionCheck( p ) and self.wrapCheck( p ) ]
				# build next dent
				if len( validPlots ) > 0:
					self.adjustBigDentsTemplate()
					plot = chooseListElement( validPlots )
					bSide = choose(66, True, False)
					namePlot = self.theBigDent( plot, bSide )			# do the other dents
					nDent += 1
					pos = chooseNumber(5)
					eTerr = dentBoni['Terrain'][pos]
					eFlat = dentBoni['Flat'][pos]
					eHills = dentBoni['Hills'][pos]
					# set landmark
					dentDict = chooseListPop( dentNames )
					dentDict['Plot'] = namePlot
					eForest = -1
					if not bPfall:
						if eTerr in [etMarsh, etGrass]:
							eForest = chooseMore( (25,efJungle), (66,efForest), (100,-1) )
						if (eForest == efJungle) and (evalLatitude(namePlot) > 60):
							eForest = efForest
					dentDict['Flat'] = [ dentDict['Flat'], eTerr, eForest, eFlat ]
					dentDict['Hills'] = [ dentDict['Hills'], eHills ]
					mapSetSign( namePlot, dentDict['Hills'][0], self.noSigns )
					self.regionNames.append( ('Dent', dentDict) )
				else:
					sprint += "[MST] No room for Dent \n"
					break
			minMap += 1

		print "[MST] %i dents built: %r" % ( nDent, self.dentList )
#		print "[MST] Regions: %r" % ( self.regionList )

	# make a big dent
	def theBigDent( self, pCenterPlot, sideways=None, chAccess=66 ):
#		print "[MST] ======== MapRegions:theBigDent()"
		if pCenterPlot==None: return None

		# deal sideways
		rot = chooseNumber( 4 )
		printDict( self.dentTemplate, "dentTemplate:", prefix="[MST] " )
		template = self.rotateTemplate( self.dentTemplate, rot )
		if not (sideways == None):
			bSide = len( template[0] ) < len( template.keys() )
			if ( sideways and (not bSide) ) or ( bSide and (not sideways) ):
				template = self.rotateTemplate( template, 1 )
				rot += 1
		printDict( template, "rotated %i" % (rot), prefix="[MST] " )
		print "[MST] Template rotated %i degrees, sideways: %r" % (rot*90, sideways)

		# get region size
		x0   = pCenterPlot.getX()
		minX = x0 + 1 - ( len( template[0] ) / 2 ) + ( len( template[0] ) % 2 )
		maxX = minX + len( template[0] ) - 1
		k = len( template.keys() )
		y0   = pCenterPlot.getY()
		minY = y0 + 1 - ( k / 2 ) + ( k % 2 )
		maxY = minY + k - 1
		namePlot = GetPlot( minX + (maxX - minX) / 2, minY + 1 + (maxY - minY) / 2 )

		# register
		bSide = len( template[0] ) < len( template.keys() )
		self.regionList.append( [x0, y0] )
		self.dentList.append( [x0, y0, bSide] )
		print "[MST] Building Big Dent @ %3i,%2i" % ( x0, y0 )

		# pass 1 - change plots
		sprint = "[MST] pass 1 - change plots \n"
		var = chooseNumber(8)		# makes some dents more mountainous than others
		chWaterFlat = 82 + var		# chance Water->Flat
		chFlatHill  = 63 + var		# chance Flat->Hill
		chHillPeak  = 63 + var		# chance Hill->Peak
		chTundra      = 66           # chance for snow terrain
		chTaiga    = 60           # chance for tundra terrain
		chVolcano   =  5				# chance for volcano for each of the 15 center plots
		chRiver     = 30				# chance for river
		bHasVolcano = False

		for dx in range( minX, maxX + 1 ):
			for dy in range( minY, maxY + 1 ):
				temp = template[dy-minY][dx-minX]
				if temp==0: continue																# ignore
				plot = plotXY( dx, dy, 0, 0 )
				if plot.isNone(): continue														# no plot -> ignore
				if temp==4:																			# hilly
					if plot.isWater():
						if choose( chWaterFlat, True, False ):
							plot.setPlotType( PlotTypes.PLOT_LAND, True, True )
#							sprint += "[MST] @ %3i,%2i: Water -> Land \n" % ( plot.getX(), plot.getY() )
					if plot.isFlatlands():
						iChance = iif( bPfall, chFlatHill/3, chFlatHill )
						if choose( iChance, True, False ):
							plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
#							sprint += "[MST] @ %3i,%2i: Flat -> Hills \n" % ( plot.getX(), plot.getY() )
					if plot.isHills():
						iChance = iif( bPfall, (100-chHillPeak)/3, (100-chHillPeak) )
						if choose( iChance, True, False ):
							plot.setPlotType( PlotTypes.PLOT_PEAK, True, True )
#							sprint += "[MST] @ %3i,%2i: Hills -> Peak \n" % ( plot.getX(), plot.getY() )
				if temp==3:																			# hills or peaks
					if plot.isWater():
						iChance = (100-chWaterFlat)*(100-chWaterFlat)/100
						if choose( iChance, False, True ):
							plot.setPlotType( PlotTypes.PLOT_LAND, True, True )
#							sprint += "[MST] @ %3i,%2i: Water -> Land \n" % ( plot.getX(), plot.getY() )
					if plot.isFlatlands():
						iChance = iif( bPfall, chFlatHill/2, chFlatHill )
						if choose( iChance, True, False ):
							plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
#							sprint += "[MST] @ %3i,%2i: Flat -> Hills \n" % ( plot.getX(), plot.getY() )
					if plot.isHills():
						iChance = iif( bPfall, chHillPeak/2, chHillPeak )
						if choose( iChance, True, False ):
							plot.setPlotType( PlotTypes.PLOT_PEAK, True, True )
#							sprint += "[MST] @ %3i,%2i: Hills -> Peak \n" % ( plot.getX(), plot.getY() )
				if temp==2:																			# mountainous
					if plot.isWater():
						plot.setPlotType( PlotTypes.PLOT_LAND, True, True )
#						sprint += "[MST] @ %3i,%2i: Water -> Land \n" % ( plot.getX(), plot.getY() )
					if plot.isFlatlands():
						iChance = (100-chFlatHill)*(100-chFlatHill)/100
						if choose( iChance, False, True ):
							plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
#							sprint += "[MST] @ %3i,%2i: Flat -> Hills \n" % ( plot.getX(), plot.getY() )
					if plot.isHills():
						if choose( chHillPeak, True, False ):
							plot.setPlotType( PlotTypes.PLOT_PEAK, True, True )
#							sprint += "[MST] @ %3i,%2i: Hills -> Peak \n" % ( plot.getX(), plot.getY() )
				if temp==1:																			# peaks and volcanos
					if plot.isWater():
						plot.setPlotType( PlotTypes.PLOT_LAND, True, True )
#						sprint += "[MST] @ %3i,%2i: Water -> Land \n" % ( plot.getX(), plot.getY() )
					if plot.isFlatlands():
						iChance = (100-chFlatHill)*(100-chFlatHill)/100
						if choose( iChance, False, True ):
							plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
#							sprint += "[MST] @ %3i,%2i: Flat -> Hills \n" % ( plot.getX(), plot.getY() )
					if plot.isHills():
						iChance = (100-chHillPeak)*(100-chHillPeak)/100
						if choose( iChance, False, True ):
							plot.setPlotType( PlotTypes.PLOT_PEAK, True, True )
#							sprint += "[MST] @ %3i,%2i: Hills -> Peak \n" % ( plot.getX(), plot.getY() )

		# pass 2 - make accessable
		sprint += "[MST] pass 2 - make accessable \n"
		chAccess2 = chAccess - 15 + chooseNumber( 30 )
		if chAccess2 > 0:
			for dx in range( minX, maxX + 1 ):
				for dy in range( minY, maxY + 1 ):
					if numPeakNeighbors( dx, dy ) == 8:
						eOpen = chooseNumber( DirectionTypes.NUM_DIRECTION_TYPES )
						pl = plotDirection( dx, dy, DirectionTypes(eOpen) )
						if not pl.isNone():
							if choose( chAccess2, True, False ):
								pl.setPlotType( PlotTypes.PLOT_HILLS, True, True )
					elif numPeakNeighbors( dx, dy ) == 7:
						eOpen = chooseNumber( DirectionTypes.NUM_DIRECTION_TYPES )
						pl = plotDirection( dx, dy, DirectionTypes(eOpen) )
						if not pl.isNone():
							if choose( chAccess2/2, True, False ):
								pl.setPlotType( PlotTypes.PLOT_HILLS, True, True )

		# pass 3 - change terrain
		sprint += "[MST] pass 3 - change terrain \n"
		for dx in range( minX, maxX + 1 ):
			for dy in range( minY, maxY + 1 ):
				temp = template[dy-minY][dx-minX]
				plot = plotXY( dx, dy, 0, 0 )
				if plot.isNone(): continue														# no plot -> ignore
				if bPfall:
					if temp==0: continue
					if temp==1:
						plot.setTerrainType( etRockyPolar, True, True )
					if temp==2 or temp==3:
						if plot.getTerrainType()==etFlatPolar:
							plot.setTerrainType( etRockyPolar, True, True )
						elif plot.getTerrainType()==etFlatArid:
							plot.setTerrainType( etRockyArid, True, True )
						elif plot.getTerrainType()==etFlatMoist:
							plot.setTerrainType( etRockyMoist, True, True )
						elif plot.getTerrainType()==etFlatRainy:
							plot.setTerrainType( etRockyRainy, True, True )
				else:
					if temp==1:
						if plot.isFlatlands():
							plot.setTerrainType( etGrass, True, True )
						else:
							plot.setTerrainType( etTundra, True, True )
					elif temp==2:
						if plot.getTerrainType() == etTundra: continue
						iChance = chTundra
						if evalLatitude( plot ) < 25: iChance = 100 - chTundra
						if choose( iChance, True, False ):
							plot.setTerrainType( etTundra, True, True )
						else:
							plot.setTerrainType( etTaiga, True, True )
					elif temp==3:
						if plot.getTerrainType() == etTundra: continue
						if plot.getTerrainType() == etTaiga: continue
						iChance = chTaiga
						if evalLatitude( plot ) < 30: iChance = 100 - chTaiga
						if choose( iChance, True, False ):
							plot.setTerrainType( etTaiga, True, True )
						elif plot.getTerrainType() == etDesert:
							plot.setTerrainType( etPlains, True, True )
					if plot.isHills():											# no marsh on hills
						if plot.getTerrainType()==etMarsh:
							plot.setTerrainType( etGrass, True, True )

		# pass 4 - add volcanos
		sprint += "[MST] pass 4 - add volcanos \n"
		if bVolcano:
			for dx in range( minX, maxX + 1 ):
				for dy in range( minY, maxY + 1 ):
					plot = plotXY( dx, dy, 0, 0 )
					if bHasVolcano: break
					if plot.isNone(): continue														# no plot -> ignore
					if plot.isPeak():
						if choose( chVolcano, True, False ):
							plot.setFeatureType( efVolcano, -1 )
							self.dentVolcanos.append( plot )
							bHasVolcano = True
							sprint += "[MST] Volcano @ %3i,%2i \n" % ( plot.getX(), plot.getY() )

		# pass 5 - add rivers
		sprint += "[MST] pass 5 - add rivers \n"
		print sprint
		sprint = ""
		bSkip = False
		iCnt = 0
		for dx in range( minX, maxX + 1 ):
			for dy in range( minY, maxY + 1 ):
				if bSkip:
					bSkip = False
					continue
				elif iCnt > 2:
					break
				plot = plotXY( dx, dy, 0, 0 )
				if plot.isNone(): continue														# no plot -> ignore
				if not riverMaker.hasCoastAtSECorner( plot ):
					if choose( chRiver, True, False ):
						rList = []
						if (dy<=0) and (dx==0):
							riverMaker.buildRiver( plot, True, choose(50,ecEast,ecSouth), riverList=rList )
						elif (dy<=0) and (dx==-1):
							riverMaker.buildRiver( plot, True, choose(50,ecWest,ecSouth), riverList=rList )
						elif (dy>=2) and (dx==0):
							riverMaker.buildRiver( plot, True, choose(50,ecEast,ecNorth), riverList=rList )
						elif (dy>=2) and (dx==-1):
							riverMaker.buildRiver( plot, True, choose(50,ecWest,ecNorth), riverList=rList )
						elif (dy==1) and (dx==0):
							riverMaker.buildRiver( plot, True, ecEast, riverList=rList )
						elif (dy==1) and (dx==-1):
							riverMaker.buildRiver( plot, True, ecWest, riverList=rList )
						bSkip = True
						iCnt += 1
						sprint += riverMaker.outRiverList( rList, "[MST]" )
						if self.dentRivers==None: self.dentRivers = []
						self.dentRivers.append( rList )
		print sprint
		return namePlot

	#---------------------------------------------------
	#        ........    ........              Ww Water
	#  dy+5  .wwwGee.    .ffdpaa.   dy+5       Ff Fire
	#  dy+4  .wWmgEe.    .fFddAa.   dy+4       Aa Air
	#  dy+3  .wwmPDP.    .dDpggg.   dy+3       Ee Earth
	#  dy+2  .gggpDd.    .PDPmww.   dy+2       Dd Desert
	#  dy+1  .aAddFf.    .eEgmWw.   dy+1       Pp Plains
	#  dy    .aapdff.    .eeGwww.   dy         Gg Grass
	#        ........    ........              m  Marsh
	#         !    !      !    !
	#        dx  dx+5    dx  dx+5
	#---------------------------------------------------
	# build an 'Elemental Quarter' according to one of the the templates
	# with the four center plots having crystallized mana nodes
	def buildElementalQuarter( self, chEQ=66 ):
		print "[MST] ===== MapRegions:buildElementalQuarter()"
		minOcean = 25
		if not bFFH:
			print "[MST] No elemental magic in this mod"
			return
		if chEQ == 0:
			print "[MST] No Elemental Quarter selected"
			return
		if not choose( chEQ, True, False ):
			print "[MST] No Elemental Quarter choosen"
			return
		if marshMaker.bModHasMarsh == None: marshMaker.initialize()
		# get valid plots
		validPlots = []
		for x in range( 5, iNumPlotsX-5 ):
			for y in range( 5, iNumPlotsY-5 ):
				plot = map.plot(x,y)
				if plot.isWater() and (numWaterNeighbors(x, y) < 8):
					if (evalLatitude( plot ) < 80) and (evalLatitude( plot ) > 10):
						if plot.area().getNumTiles() >= minOcean:
							if self.regionCheck( plot ):
								x,y = plot.getX(), plot.getY()
								pl = plotDirection( x, y, DirectionTypes.DIRECTION_NORTHWEST )
								if pl.isWater() and (numWaterNeighbors(pl.getX(), pl.getY()) == 8):
									pl = plotDirection( x, y, DirectionTypes.DIRECTION_SOUTHEAST )
									if not pl.isWater():
										fx, fy = pl.getX(), pl.getY()
										validPlots.append( (fx, fy, 0) )
								pl = plotDirection( x, y, DirectionTypes.DIRECTION_NORTHEAST )
								if pl.isWater() and (numWaterNeighbors(pl.getX(), pl.getY()) == 8):
									pl = plotDirection( x, y, DirectionTypes.DIRECTION_SOUTHWEST )
									if not pl.isWater():
										fx, fy = pl.getX(), pl.getY()
										validPlots.append( (fx-1, fy, 1) )
								pl = plotDirection( x, y, DirectionTypes.DIRECTION_SOUTHEAST )
								if pl.isWater() and (numWaterNeighbors(pl.getX(), pl.getY()) == 8):
									pl = plotDirection( x, y, DirectionTypes.DIRECTION_NORTHWEST )
									if not pl.isWater():
										fx, fy = pl.getX(), pl.getY()
										validPlots.append( (fx-1, fy+1, 2) )
								pl = plotDirection( x, y, DirectionTypes.DIRECTION_SOUTHWEST )
								if pl.isWater() and (numWaterNeighbors(pl.getX(), pl.getY()) == 8):
									pl = plotDirection( x, y, DirectionTypes.DIRECTION_NORTHEAST )
									if not pl.isWater():
										fx, fy = pl.getX(), pl.getY()
										validPlots.append( (fx, fy+1, 3) )
		# build Elemental Quarter
		printList(validPlots, "Valid Plots", prefix="[MST] ")
		if len( validPlots ) > 0:
			x, y, rot = chooseListElement( validPlots )
			plot = map.plot(x, y)
			template = self.rotateTemplate( self.eqTemplate, rot )
			printDict( self.eqTemplate, prefix="[MST] " )
			self.theElementalQuarter( plot, template, rot )
			printDict( template, "rotated %i" % (rot), prefix="[MST] " )
			self.regionNames.append( ('EQ', "Elemental Quarter", plot) )
		else:
			print "[MST] No valid plot found for 'Elemental Quarter'"
			return
#		print "[MST] 'Elemental Quarter' built: %r" % ( self.eqList )
#		print "[MST] Regions: %r" % ( self.regionList )

	# build the 'Elemental Quarter'
	def theElementalQuarter( self, pCenterPlot, template, rotation ):
#		print "[MST] ===== MapRegions:elementalQuarter()"
		if pCenterPlot==None: return
		# get coordinates
		x0 = pCenterPlot.getX()
		y0 = pCenterPlot.getY()
		# register
		self.regionList.append( [x0, y0] )
		self.eqList.append( [x0, y0, template, rotation] )
		# make
		print "[MST] Building 'Elemental Quarter' @ %3i,%2i \n\n" % ( x0, y0 )
#		printDict( template, prefix="[MST] " )
		self.stampElementalQuarter()		# not needed if rivers are handled properly
		return pCenterPlot

	# add names and boni to regions
	def addRegionExtras( self ):
		print "[MST] ===== MapRegions:addRegionExtras()"
		if len( self.lostIsleList ) > 0: self.addLostIsleExtras()
		if len( self.bogList ) > 0: self.addBigBogExtras()
		if len( self.dentList ) > 0: self.addBigDentExtras()
		if len( self.eqList ) > 0: self.addElementalQuarterExtras()
		return

	###############
	### Helpers ###
	###############

	# adjust BigDent for mapsize
	def adjustBigDentsTemplate( self, bRandom=False ):
		print "[MST] ======== MapRegions:adjustBigDentsTemplate()"
		siz = iif( bRandom, chooseNumber( 7 ), map.getWorldSize() )
		#printDict( self.bigDentTemplate, "before:", prefix="[MST] " )
		self.dentTemplate = self.bigDentTemplate.copy()
		if (siz < 5) and choose(80, True, False):			# duel - large
			del self.dentTemplate[ 5 ]
		if (siz < 4) and choose(80, True, False):			# duel - standard
			del self.dentTemplate[ 3 ]
		if (siz < 3) and choose(80, True, False):			# duel - small
			for i in self.dentTemplate.keys(): del self.dentTemplate[i][8]
		if (siz < 2) and choose(80, True, False):			# duel - tiny
			for i in self.dentTemplate.keys(): del self.dentTemplate[i][6]
		#printDict( self.dentTemplate, "after:", prefix="[MST] " )

	# rotate template dictionary; steps are 0,1,2,3 clockwise
	# corresponding to rotations by 0,90,180,270 degrees
	# - new keys are integers starting with 0
	# - returns new template, old template is not touched
	def rotateTemplate( self, tempDict, steps ):
		#print "[MST] ======== MapRegions:rotateTemplate()"
		steps = steps % 4
		if steps == 0: steps = 4		# to ensure that new template has continuous integers as keys
		temp = tempDict.copy()
		keyList = temp.keys()
		keyList.sort()
		maxLen = 0
		for k in keyList: maxLen = max( maxLen, len( tempDict[k] ) )
		if maxLen > 0:
			for i in range( steps ):
				newTemp = {}
				for v in range( maxLen-1, -1, -1 ):
					newTemp[ v ] = []
					for k in keyList:
						val = temp[k]
						if v >= len( val ):
							elem = None
						else:
							elem = val[v]
						newTemp[v].append( elem )
				temp = newTemp
				maxLen = len( keyList )
				keyList = temp.keys()
				keyList.sort()
		return temp

	# add names, boni, improvements and other late extras to region: 'theLostIsle'
	def addLostIsleExtras( self ):
		print "[MST] ======== MapRegions:addLostIsleExtras()"

		lostIsleNames = [ "Niflheim", "Atlantis", "Numenor",
						  "Minos", "Rillanon", "Ensligholm" ]
		lostIsleNames_Pfall = [ "Alien HQ", "Command Center", "City of Light", "Atlantis Command" ]

		sprint = ""
		for x0,y0,pList,bAliens in self.lostIsleList:
			plDone = []

			# volcano
			if bVolcano:
				pListPeak = [ GetPlot(x,y) for x,y in pList if GetPlot(x,y).isPeak() ]
				if len(pListPeak) > 0:
					vpl = chooseListElement( pListPeak )
					vpl.setFeatureType( efVolcano, -1 )
					sprint += "[MST] Placed volcano @ (%r,%r)\n" % (vpl.getX(),vpl.getY())

			# city ruins
			printList( pList, "Lost Isle Tiles:", prefix="[MST] " )
			pListCoast = [ GetPlot(x,y) for x,y in pList
						   if (not GetPlot(x,y).isPeak()) and GetPlot(x,y).isCoastalLand() ]
			plot = chooseListElement( pListCoast )
			if plot == None:
				print "[MST] Unable to place City Ruins"
				continue
			cx = plot.getX()
			cy = plot.getY()
			plot.setBonusType( -1 )
			plot.setImprovementType( eiCityRuins )
			sprint += "[MST] Placed City Ruins @ (%r,%r)\n" % (cx, cy)
			bonusBalancer.balanceBoniAtPlot( plot, maxPass = 2 )

			# river
			rList = []
			riverDirs = riverMaker.checkRiverEnd( plot, bDownFlow=True )
			rDir = chooseListElement( riverDirs )
			if rDir != None:
				riverMaker.buildRiver( plot, False, rDir, riverList=rList )		# upFlow
				print riverMaker.outRiverList( rList, "[MST] " )
			else:
				print "[MST] Unable to build river"

			# improve terrain
			pListTer = [ GetPlot(x,y) for x,y in pList if not GetPlot(x,y).isPeak() ]
			for pl in pListTer:
				if bPfall:
					if pl.getTerrainType() == etFlatPolar:
						newTerrain = chooseMore( (20,etFlatPolar), (80,etFlatMoist), (100,etFlatRainy) )
						pl.setTerrainType( newTerrain, True, True )
					elif pl.getTerrainType() == etRockyPolar:
						newTerrain = chooseMore( (20,etRockyPolar), (80,etRockyMoist), (100,etRockyRainy) )
						pl.setTerrainType( newTerrain, True, True )
					elif pl.getTerrainType() == etFlatArid:
						newTerrain = choose( 20, etFlatArid, etFlatMoist )
						pl.setTerrainType( newTerrain, True, True )
					elif pl.getTerrainType() == etRockyArid:
						newTerrain = choose( 20, etRockyArid, etRockyMoist )
						pl.setTerrainType( newTerrain, True, True )
				else:
					if pl.getTerrainType() == etTundra:
						newTerrain = chooseMore( (20,etGrass), (85,etTaiga), (100,etTundra) )
						if pl.isFreshWater():
							newTerrain = chooseMore( (25,etMarsh), (75,newTerrain), (100,etGrass) )
						pl.setTerrainType( newTerrain, True, True )
					elif pl.getTerrainType() == etTaiga:
						if pl.isFreshWater():
							newTerrain = chooseMore( (30,etGrass), (60,etMarsh), (100,etTaiga) )
						else:
							newTerrain = chooseMore( (30,etGrass), (100,etTaiga) )
						pl.setTerrainType( newTerrain, True, True )
					elif pl.getTerrainType() == etDesert:
						newTerrain = choose( 20, etGrass, etPlains )
						if not pl.isFreshWater() and not plot.isCoastalLand():
							newTerrain = choose( 25, etDesert ,newTerrain )
						pl.setTerrainType( newTerrain, True, True )

			# place boni and work them
			pListBoni = [ GetPlot(x,y) for x,y in pList
												if ( (x,y) != (cx,cy) ) and
												   ( not GetPlot(x,y).isPeak() ) ]
			if bPfall:
				bonList = [ ebFungicide, ebFungalGin, ebGrenadeFruits,
							[ebRareDnaMoist, ebRareDnaRainy], ebArtifact, ebThorium,
							ebMineral, ebEnergy, ebGold ]
			elif bFFH:
				bonList = [ [ebGold, ebSilver], [ebGems, ebCoal], ebMithril,
							   [ebCopper, ebIron], [ebSheep, ebCow], ebReagens,
							   ebMana, ebManaChaos, [ebManaDeath, ebManaEntropy] ]
			else:
				bonList = [ ebGold, ebGems, ebSilver,
							   [ebCopper, ebIron], ebOil, [ebSheep, ebCow],
							   ebCoal, ebSulphur, ebUranium ]
			chance = iif( bAliens, 90, 60 )
			# try for four landbased boni on the island
			for i in range(4):
				# get bonus
				bon = chooseListPop( bonList )
				if isList(bon):
					bon = chooseListElement( bon )
				if bon < 0: continue
				# get plot for bonus
				pBoni = [ pl for pl in pListBoni
							 if ( pl.getBonusType(-1) == -1 ) and
								( pl.canHaveBonus(bon, False) ) ]
				pl = chooseListPop( pBoni )
				if pl == None: continue			# bonus forbidden on island
				pl.setBonusType( bon )
				# work placed boni
				if choose( chance, True, False ):
					bonString = gc.getBonusInfo(bon).getType()
					bonTech = gc.getBonusInfo(bon).getTechCityTrade()
					bonEra = 0
					if bonTech > -1:
						bonEra = gc.getTechInfo(bonTech).getEra()
					if bonEra < 0: bonEra = 0
					eraString =	gc.getEraInfo(bonEra).getType()
					sprint += "[MST] Improve %s @ (%r,%r) - Era: %s\n" % (bonString,pl.getX(),pl.getY(),eraString)
					# find possible improvements for boni
					impList = [ (bonEra, imp) for imp in range(gc.getNumImprovementInfos())
													  if pl.canHaveImprovement(imp, TeamTypes.NO_TEAM, True) and
														 gc.getImprovementInfo(imp).isImprovementBonusMakesValid(bon) ]
					if len(impList) == 0:
						sprint += "[MST] No improvement found for %s @ (%r,%r)\n" % (bonString,pl.getX(),pl.getY())
						continue
					impList.sort()
					if bAliens:
						bonEra, imp = impList[ len(impList)-1 ]		# highest tech
					else:
						bonEra, imp = impList[ 0 ]
						if bonEra > 1:
							sprint += "[MST] Civ to primitive to work %s @ (%r,%r)\n" % (bonString,pl.getX(),pl.getY())
							continue												# ancient and classic tech only
					impString = gc.getImprovementInfo(imp).getType()
					pl.setImprovementType( imp )
					sprint += "[MST] Placed %s on %s @ (%r,%r)\n" % (impString,bonString,pl.getX(),pl.getY())
			print sprint

			# city area - improvements
			chance = iif( bAliens, 80, 50 )
			featList = [ efJungle ]
			if not bPfall: featList = [ efForest, efJungle ]
			if bFFH: featList = featList + [ efForestNew, efForestAncient ]
			impTuple = ( eiFarm, eiMine )
			if bAliens: impTuple = ( eiWindmill, eiFarm, eiMine )
			if bPfall:
				impTuple = ( eiSolarCollector, eiMine, eiGreenhouse )
				rocky = [ etRockyRainy, etRockyMoist, etRockyArid, etRockyPolar, ]
			sprint = ""
			pListCity = [ GetPlot(x,y) for x,y in pList
						  if plotDistance(x, y, cx, cy) == 1 ]

			for pl in pListCity:
				for imp in impTuple:
					if pl.isWater(): continue
					if pl.getBonusType(-1) > -1: continue
					if pl.getFeatureType() in featList:
						pl.setFeatureType( FeatureTypes.NO_FEATURE, -1 )
					if pl.canHaveImprovement( imp, TeamTypes.NO_TEAM, True ):
						if choose( chance, True, False ): continue
						if bPfall:
							if (imp == eiSolarCollector) and choose(25, True, False): continue
							if (imp == eiMine) and (imp not in rocky): continue
							impString = gc.getImprovementInfo(imp).getType()
							pl.setImprovementType( imp )
							sprint += "[MST] Placed %s @ (%r,%r)\n" % (impString,pl.getX(),pl.getY())
						else:
							impString = gc.getImprovementInfo(imp).getType()
							pl.setImprovementType( imp )
							sprint += "[MST] Placed %s @ (%r,%r)\n" % (impString,pl.getX(),pl.getY())

			# city area - Goody Hut
			for pl in pListCity:
				if pl.isWater(): continue
				if pl.isPeak(): continue
				if choose(33,True,False): continue
				pl.setImprovementType( eiGoody )
				sprint += "\n[MST] Goody Hut placed @ (%r,%r)\n\n" % (pl.getX(),pl.getY())
				break

			# city area - roads
			chance = iif( bAliens, 90, 60 )
			eRoad = gc.getInfoTypeForString('ROUTE_ROAD')
			if bAliens: eRoad = gc.getNumRouteInfos() - 1
			roadString = gc.getRouteInfo(eRoad).getType()
			for pl in pListCity:
				if pl.isWater(): continue
				if pl.isPeak(): continue
				if pl.getBonusType(-1) >= 0:
					pl.setRouteType( eRoad )
				else:
					if choose( chance, False, True ): continue
					pl.setRouteType( eRoad )
				sprint += "[MST] Placed %s @ (%r,%r)\n" % (roadString,pl.getX(),pl.getY())

			# isle area - roads
			chance = iif( bAliens, 66, 25 )
			eRoad = gc.getInfoTypeForString('ROUTE_ROAD')
			roadString = gc.getRouteInfo(eRoad).getType()
			for x,y in pList:
				pl = GetPlot(x,y)
				if pl in pListCity: continue
				if pl.isWater(): continue
				if pl.isPeak(): continue
				if pl.getBonusType(-1) >= 0:
					pl.setRouteType( eRoad )
				else:
					if choose( chance, False, True ): continue
					pl.setRouteType( eRoad )
				sprint += "[MST] Placed %s @ (%r,%r)\n" % (roadString,pl.getX(),pl.getY())

			# city area - fishes
			wList = []
			if bPfall:
				bonList = [ ebAlgaeCyan, ebEnergy, ebMineral ]
			else:
				bonList = [ ebFish, ebCrab ]
			pListWater = [ GetPlot(x,y) for x in range(cx-1,cx+2) for y in range(cy-1,cy+2) if GetPlot(x,y).isWater()]
			pl = chooseListElement( pListWater )
			if pl == None:
				sprint += "\n[MST] No water-boni placed"
			else:
				bon = chooseListElement( bonList )
				pl.setBonusType( bon )
				bonString = gc.getBonusInfo(bon).getType()
				sprint += "\n[MST] Placed %s @ (%r,%r)" % (bonString,pl.getX(),pl.getY())

			# name
			nam = chooseListPop( lostIsleNames )
			if bPfall:
				nam = chooseListPop( lostIsleNames_Pfall )
			CyEngine().removeLandmark( GetPlot(x0,y0) )			# remove 'Lost Isle' sign
			print sprint
			print "[MST] " + mapSetSign( GetPlot(cx,cy), nam, self.noSigns )

	# add names, boni and other late extras to region: 'theBigBog'
	def addBigBogExtras( self ):
		print "[MST] ======== MapRegions:addBigBogExtras()"
		bDarkLake = False
		bDarkMoor = False
		sprint = ""
		for reg in self.regionNames:
			# BigBog Names
			if reg[0] == 'Bog':
				plot = reg[2]
				if reg[1] == "Big Bog":
					if plot.isWater():
						sprint += "[MST] " + mapSetSign( plot, "Big Bog Lake", self.noSigns )
						if choose( 33, True, False ):
							if not bPfall:
								plot.setBonusType( chooseMore( (66,ebFish), (100,ebClam) ) )
					else:
						sprint += "[MST] " + mapSetSign( plot, "The Big Bog", self.noSigns )
				elif reg[1] == "Darkwater":
					if plot.isWater():
						if not bDarkLake:
							sprint += "[MST] " + mapSetSign( plot, "Darkwater Lake", self.noSigns )
							bDarkLake = True
							if choose( 20, True, False ):
								if not bPfall:
									plot.setBonusType( chooseMore( (66,ebFish), (100,ebClam) ) )
						else:
							sprint += "[MST] " + mapSetSign( plot, "Darkwater Basin", self.noSigns )
					else:
						if not bDarkMoor:
							sprint += "[MST] " + mapSetSign( plot, "Darkwater Moor", self.noSigns )
							bDarkMoor = True
						else:
							sprint += "[MST] " + mapSetSign( plot, "Darkwater Swamp", self.noSigns )
		print sprint
		return

	# add names, boni and other late extras to region: 'theBigDent'
	def addBigDentExtras( self ):
		print "[MST] ======== MapRegions:addBigDentExtras()"
		sprint = ""
		for reg in self.regionNames:
			# BigDent Names
			if reg[0] == 'Dent':
				dDict = reg[1]
				dPlot = dDict['Plot']
				if dPlot.isPeak():
					sprint += "[MST] " + mapSetSign( dPlot, dDict['Peak'], self.noSigns )
					if bVolcano:
						if dPlot.getFeatureType() == efVolcano:
							sprint += "[MST] " + mapSetSign( dPlot, dDict['Volcano'], self.noSigns )
					elif bVolcanoDormant:
						if dPlot.getFeatureType() == efVolcanoDormant:
							sprint += "[MST] " + mapSetSign( dPlot, dDict['Volcano'], self.noSigns )
				elif dPlot.isWater():
					sprint += "[MST] " + mapSetSign( dPlot, dDict['Water'], self.noSigns )
				elif dPlot.isFlatlands():
					if dDict['Flat'][1] != None:
						dPlot.setTerrainType( dDict['Flat'][1], True, True )
					if dDict['Flat'][2] != None:
						dPlot.setFeatureType( dDict['Flat'][2], -1 )
					if dDict['Flat'][3] != None:
						if dPlot.getBonusType(-1) == -1:
							if bonusBalancer.isBonusValid( dDict['Flat'][3], dPlot, True, True, True ):
								bonusBalancer.placeBonus( dPlot, dDict['Flat'][3] )
					sprint += "[MST] " + mapSetSign( dPlot, dDict['Flat'][0], self.noSigns )
					if choose(66,True,False):
						dPlot.setImprovementType( eiGoody )
						sprint += "[MST] Goody Hut placed @ (%r,%r)" % (dPlot.getX(),dPlot.getY())
				elif dPlot.isHills():
					if dDict['Hills'][1] != None:
						if dPlot.getBonusType(-1) == -1:
							if bonusBalancer.isBonusValid( dDict['Hills'][1], dPlot, True, True, True ):
								bonusBalancer.placeBonus( dPlot, dDict['Hills'][1] )
					sprint += "[MST] " + mapSetSign( dPlot, dDict['Hills'][0], self.noSigns )
		print sprint

	# add mana, restamp terrain/plots and kill boni and features
	def addElementalQuarterExtras( self ):
		print "[MST] ======== MapRegions:addElementalQuarterExtras()"
		sprint = ""
		for reg in self.regionNames:
			# Elemental Quarter Name
			if reg[0] == 'EQ':
				plot = reg[2]
				x,y = plot.getX(), plot.getY()
				sPlot = map.plot(x,y)
				if reg[1] == "Elemental Quarter":
					sprint += "[MST] " + mapSetSign( sPlot, "Elemental Quarter", self.noSigns )
			# extras; do it again as things may have changed
			self.stampElementalQuarter()
		print sprint

	# check, if regioncenter is far enough away from other regions to be placed at plot
	def regionCheck( self, plot ):
#		print "[MST] ======== MapRegions:regionCheck()"
		bValid = True
		iMinDist = self.regionDist + 3 * map.getWorldSize()
		x0 = plot.getX()
		y0 = plot.getY()
		for dx,dy in self.regionList:
			iDist = plotDistance( x0, y0, dx, dy )
			if iDist < iMinDist:
				bValid = False
				break
		return bValid

	# check thet plot is not within dist plots from the edges
	def wrapCheck( self, plot, dist=3 ):
#		print "[MST] ======== MapRegions:wrapCheck()"
		x,y = coordByPlot( plot )
		if not map.isWrapX():
			if (x < dist) or (x > (iNumPlotsX-1-dist)): return False
		if not map.isWrapY():
			if (y < dist) or (y > (iNumPlotsY-1-dist)): return False
		return True

	# delete plots which can't be bog centers
	def deleteNonBogPlots( self, plotList ):
#		print "[MST] ======== MapRegions:deleteNonBogPlots()"
		for inx in range( len(plotList)-1,-1,-1 ):
			pl = plotList[inx]
			if pl.isCoastalLand():
				del plotList[inx]
			else:
				iLat = evalLatitude( pl )		# 0..90
				if bPfall:
					bZone = (marshMaker.iMarshHotBottom<=iLat and iLat<=marshMaker.iMarshHotTop) or    \
							  ((marshMaker.iMarshColdBottom-5)<=iLat and (iLat<=marshMaker.iMarshColdTop-5))
				else:
					bZone = (marshMaker.iMarshHotBottom<=iLat and iLat<=marshMaker.iMarshHotTop) or    \
							  (marshMaker.iMarshColdBottom<=iLat and iLat<=marshMaker.iMarshColdTop)
				if bZone:
					if not map.isWrapX():
						if (pl.getX()<3) or (pl.getX()>(iNumPlotsX-4)):
							del plotList[inx]
							continue
					if not map.isWrapY():
						if (pl.getY()<3) or (pl.getY()>(iNumPlotsY-4)):
							del plotList[inx]
				else:
					del plotList[inx]

	# delete plots which can't be dent centers
	def deleteNonDentPlots( self, plotList ):
#		print "[MST] ======== MapRegions:deleteNonDentPlots()"
		for inx in range( len(plotList)-1,-1,-1 ):
			pl = plotList[inx]
			if pl.isCoastalLand():
				del plotList[inx]
			else:
				if not map.isWrapX():
					if (pl.getX()<3) or (pl.getX()>(iNumPlotsX-4)):
						del plotList[inx]
				elif not map.isWrapY():
					if (pl.getY()<3) or (pl.getY()>(iNumPlotsY-4)):
						del plotList[inx]

	# change to bog-terrain
	def changeBogTerrain( self, plot, temp ):
#		print "[MST] ======== MapRegions:changeBogTerrain()"
		sprint = ""
		if temp==0: return sprint

		# change terrain
		ter = plot.getTerrainType()
		newTer = ter
		if bPfall:
			pass
		else:
			if temp==5:										# maybe hill
				if ter==etTundra:
					newTer = etTaiga
				elif ter==etDesert:
					newTer = etPlains
			if temp==4:										# probably grass
				if ter==etTundra or ter==etTaiga:
					newTer = chooseMore( (60,etGrass), (90,etMarsh), (100,etTaiga)  )	# --,60,30,10
				elif ter==etDesert:
					newTer = chooseMore( (70,etGrass), (80,etMarsh), (100,etPlains) )		# 20,70,10,--
				else:
					newTer = chooseMore( (60,etGrass), (90,etMarsh), (100,etPlains) )		# 10,60,30,--
			elif temp==3:									# probably marsh
				if ter==etTundra or ter==etTaiga:
					newTer = chooseMore( (30,etGrass), (85,etMarsh), (100,etTaiga) )		# --,30,55,15
				elif ter==etDesert:
					newTer = chooseMore( (40,etGrass), (80,etMarsh), (100,etPlains) )		# 20,40,40,--
				else:
					newTer = chooseMore( (30,etGrass), (85,etMarsh), (100,etPlains) )		# 15,30,55,--
			elif temp==2:									# marshy and flat
				if ter==etTundra or ter==etDesert:
					newTer = chooseMore( (30,etGrass), (100,etMarsh) )							# --,30,70,--
				else:
					newTer = chooseMore( (15,etGrass), (100,etMarsh) )							# --,15,85,--
			elif temp==1:									# possibly lake
					newTer = etMarsh
			plot.setTerrainType( newTer, True, True )
			sprint += "[MST] @ %3i,%2i: %s -> %s (temp:%i) \n" % \
			   (plot.getX(),plot.getY(),capWords(gc.getTerrainInfo(ter).getType()[8:]),capWords(gc.getTerrainInfo(newTer).getType()[8:]),temp)
		return sprint

	# find empty ocean and put 'Lost Isle' there
	def createLostIsle( self, minDist, bAliens ):
		print "[MST] ======== MapRegions:createLostIsle()"
		tileList = []
		dist = minDist + iif(bPfall,1,0) + iif(bAliens,1,0)

		# find empty ocean
		deepList = []
		for inx in range( map.numPlots() ):
			x,y = coordByIndex( inx )
			if not map.isWrapX:
				if (x<4) or (x>=(iNumPlotsX-4)):	continue
			if not map.isWrapY:
				if (y<4) or (y>=(iNumPlotsY-4)):	continue
			if isHighSeas( x, y, dist, bWrap=True, treshold=2 ):
				deepList.append( (x, y) )
		if len(deepList) == 0:
			return tileList

		print "[MST] Found %i possible plots for 'Lost Isle'" % ( len(deepList) )
		fx,fy = chooseListElement( deepList )

		# adjust template
		rot = chooseNumber( 4 )
		template = self.rotateTemplate( self.lostIsleTemplate, rot )
		printDict( self.lostIsleTemplate, "lostIsleTemplate:", prefix="[MST] " )
		printDict( template, "template rotated by %r degrees:" % (rot*90), prefix="[MST] " )

		# put isle into ocean by template
		tileList = self.stampLostIsle( template, (fx,fy) )		# method recalculates areas
		return tileList

	# create plots and terrain for 'Lost Isle'
	def stampLostIsle( self, template, center ):
#		print "[MST] ======== MapRegions:stampLostIsle()"
		x0, y0 = center
		stampList = []
		dx, dy = (2,2)
		tWidth = len( template[0] )
		tHeight = len( template.keys() )
		terrGen = MST_TerrainGenerator()
		featGen = MST_FeatureGenerator()
		sprint = ""
		# add island
		for x in range( tWidth ):
			for y in range( tHeight ):
				temp = template[y][x]
				fx = x0 - dx + x
				if (fx < 0) or (fx >= iNumPlotsX): continue
				fy = y0 - dy + y
				if (fy < 0) or (fy >= iNumPlotsY): continue
				tPlot = GetPlot(fx, fy)

				# get target plot_type, terrain, feature
				pType = PlotTypes.PLOT_OCEAN
				if temp == 0:
					pType = chooseMore( (10,PlotTypes.PLOT_LAND), (100,PlotTypes.PLOT_OCEAN) )
				elif temp == 1:
					pType = chooseMore( (20,PlotTypes.PLOT_HILLS), (95,PlotTypes.PLOT_LAND), (100,PlotTypes.PLOT_OCEAN) )
				elif temp == 2:
					pType = chooseMore( (20,PlotTypes.PLOT_LAND), (95,PlotTypes.PLOT_HILLS), (100,PlotTypes.PLOT_PEAK) )
				elif temp == 3:
					pType = chooseMore( (20,PlotTypes.PLOT_LAND), (50,PlotTypes.PLOT_HILLS), (100,PlotTypes.PLOT_PEAK) )
				#sprint += "[MST] xy (%r,%r), temp: %r, pType %r\n" % (fx, fy, temp, pType)

				# set target plot_type, terrain, feature
				tPlot.setPlotType( pType, False, False )
				pTerr = terrGen.generateTerrainAtPlot( fx, fy )
				tPlot.setTerrainType( pTerr, False, False )
				featGen.addFeaturesAtPlot( fx, fy )
				if pType != PlotTypes.PLOT_OCEAN:
					stampList.append( (fx,fy) )
		print sprint

		# add coast
		lFishes = [ ebClam, ebCrab, ebFish, ebShrimp ]
		for x,y in stampList:
			lCoast = [ GetPlot(fx,fy) for fx in range(x-1,x+2) for fy in range(y-1,y+2) if GetPlot(fx,fy).isWater() ]
			for pl in lCoast:
				pl.setTerrainType( etCoast, False, False)
				# add fishes
				if choose(16, True, False):
					bon = chooseListElement( lFishes )
					pl.setBonusType( bon )

		map.recalculateAreas()
		return stampList

	# set terrain and kill features for 'Elemental Quarter'
	def stampElementalQuarter( self ):
#		print "[MST] ======== MapRegions:stampElementalQuarter()"
		for x,y,template,rot in self.eqList:
			# work template; if done early, things might get overwritten
			for dx in range( 0, 6 ):
				for dy in range( 0, 6 ):
					temp = template[dy][dx]
					plot = plotXY( x-2, y-3, dx, dy )

					# kill improvements
					plot.setImprovementType( ImprovementTypes.NO_IMPROVEMENT )
					# kill boni
					plot.setBonusType( -1 )
					# kill rivers
					# --- (perhaps) later ---
					# kill features
					plot.setFeatureType( FeatureTypes.NO_FEATURE, -1 )

					# Air center: solitary peak - no features
					if temp == 'A':
						plot.setPlotType( PlotTypes.PLOT_PEAK, False, False )
					# Air: flat or water	- no features
					elif temp == 'a':
						if not plot.isWater():
							plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
					# Earth center: Mountain, Volcano if possible
					elif temp == 'E':
						plot.setPlotType( PlotTypes.PLOT_PEAK, False, False )
						if bVolcano:
							plot.setFeatureType( efVolcano, -1 )
					# Earth: hills or peak - no features
					elif temp == 'e':
						if plot.isWater() or plot.isFlatlands():
							plot.setPlotType( PlotTypes.PLOT_HILLS, False, False )
						elif plot.isHills():
							plot.setPlotType( PlotTypes.PLOT_PEAK, False, False )
					# Fire center: flat desert - no features
					elif temp == 'F':
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etDesert, True, True )
					# Fire: desert or plains - no features
					elif temp == 'f':
						if plot.isWater():
							plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						if (plot.getTerrainType() == etDesert) or (plot.getTerrainType() == etPlains):
							plot.setTerrainType( etDesert, True, True )
						else:
							plot.setTerrainType( etPlains, True, True )
					# Water center: water - no features
					elif temp == 'W':
						plot.setPlotType( PlotTypes.PLOT_OCEAN, False, False )
					# Water: water - no features
					elif temp == 'w':
						plot.setPlotType( PlotTypes.PLOT_OCEAN, False, False )
					# Desert Hills - no features
					elif temp == "D":
						plot.setPlotType( PlotTypes.PLOT_HILLS, False, False )
						plot.setTerrainType( etDesert, True, True )
					# Desert	Flat - no features
					elif temp == "d":
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etDesert, True, True )
					# Plains Hills - no features
					elif temp == "P":
						plot.setPlotType( PlotTypes.PLOT_HILLS, False, False )
						plot.setTerrainType( etPlains, True, True )
					# Plains	Flat - no features
					elif temp == "p":
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etPlains, True, True )
					# Grass Hills - no features
					elif temp == "G":
						plot.setPlotType( PlotTypes.PLOT_HILLS, False, False )
						plot.setTerrainType( etGrass, True, True )
					# Grass Flat - no features
					elif temp == "g":
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etGrass, True, True )
					# Marsh Flat - no features
					elif temp == "m":
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etMarsh, True, True )
			for dx in range( 2, 4 ):
				for dy in range( 2, 4 ):
					temp = template[dy][dx]
					plot = plotXY( x-2, y-3, dx, dy )
					if temp == "m":
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etMarsh, True, True )
						plot.setBonusType( ebManaWater )
					if temp == "P":
						plot.setPlotType( PlotTypes.PLOT_HILLS, False, False )
						plot.setTerrainType( etPlains, True, True )
						plot.setBonusType( ebManaEarth )
					if temp == "p":
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etPlains, True, True )
						plot.setBonusType( ebManaFire )
					if temp == "g":
						plot.setPlotType( PlotTypes.PLOT_LAND, False, False )
						plot.setTerrainType( etGrass, True, True )
						plot.setBonusType( ebManaAir )
		map.recalculateAreas()

###############################################################################################################
### CLASS MapRegions END
###############################################################################################################
mapRegions = MapRegions()


#########################################################################################################
########## CLASS FeaturePlacer - put mod-dependent features on the map
#########################################################################################################
##### idea and most of placeCrystalPlains() by Operas
##### 'Orbis-friendly map scripts' --> http://forums.civfanatics.com/showthread.php?t=321920
#########################################################################################################
# placeKelp( chKelp=20, bAll=False, bLakes=False )
# placeHauntedLands( chHaunted=6 )
# placeCrystalPlains( chCrystal=25 )
#########################################################################################################
class FeaturePlacer:

	# put kelp on coast of continents; if not bAll: only near 2nd biggest continent
	def placeKelp( self, chKelp=20, bAll=False, bLakes=False ):
		if bPfall: return														# no placement on Planetfall
		if not bKelp: return													# no Kelp -> no placement
		print "[MST] ===== FeaturePlacer:placeKelp()"
		cnt = 0
		if bAll:
			# all continents
			for inx in range( map.numPlots() ):
				pl = map.plotByIndex( inx )
				if pl.isWater():
					if pl.isLake() and ( not bLakes ): continue			# lakes allowed?
					ter = pl.getTerrainType()
					if ter == etCoast:
						if pl.getFeatureType() == -1:
							if choose( chKelp, True, False ):
								pl.setFeatureType( efKelp, -1 )
								cnt += 1
		else:
			# only 2nd largest continent
			minContinent = 10
			areaList = getBigAreas( 2, False, None, minContinent )			# [ num, id, plotlist ]
			if len( areaList ) > 0:
				continentPlots = areaList[ len(areaList)-1 ][ 2 ]
				coastPlots = getContinentCoast( continentPlots, bLakes )
				for pl in coastPlots:
					if pl.getFeatureType() == -1:
						if choose( chKelp, True, False ):
							pl.setFeatureType( efKelp, -1 )
							cnt += 1
		if cnt>0: print "[MST] %i Kelp placed" % ( cnt )

	# put 'Haunted Lands': deep in forrest/jungle, near mountain passes, near city-ruins,
	# middle of desert, around and within marshes, on small islands
	# use only after starting-plots are generated
	def placeHauntedLands( self, chHaunted=6 ):
		if not bHauntedLands: return														# no Haunted Lands -> no placement
		print "[MST] ===== FeaturePlacer:placeHauntedLands()"
		minDist = 8
		# find possible plots for 'Haunted Lands'
		cnt = 0
		hauntedPlots = []
		for inx in range( map.numPlots() ):
			pl = map.plotByIndex( inx )
			x, y = coordByIndex( inx )
			# check for water and mountains
			if pl.isWater() or pl.isPeak(): continue
			# check for 'Oasis' and 'Volcano'
			if pl.getFeatureType() == efOasis: continue
			if pl.getFeatureType() == efVolcano: continue
			# check for nearby starting-plot
			if startingPlotDistance( x, y ) < minDist: continue
			# check small island
			if pl.area().getNumTiles() <= 2:
				hauntedPlots.append( pl )
				continue
			# check ruins
			if pl.getImprovementType() == eiCityRuins:								# double chance on ruins
				hauntedPlots.append( pl )
				hauntedPlots.append( pl )
				continue
			elif numNeighborType( x, y, 'IMPROVEMENT', eiCityRuins ) > 0:
				hauntedPlots.append( pl )
				continue
			# check passes
			if isMountainPass( pl, False ):
				hauntedPlots.append( pl )
				continue
			# check deep forest/jungle
			if numFeatureNeighbors( x, y, [efForest, efJungle], 1 ) == 8:
				if numFeatureNeighbors( x, y, [efForest, efJungle], 2 ) >= 18:
					hauntedPlots.append( pl )
					continue
			# check deep desert
			if numNeighborType( x, y, 'TERRAIN', etDesert, 1 ) == 8:
				if numNeighborType( x, y, 'TERRAIN', etDesert, 2 ) >= 18:
					hauntedPlots.append( pl )
					continue
			# check around marshes
			if bMarsh:
				if numNeighborType( x, y, 'TERRAIN', etMarsh, 1 ) == 8:			# double chance middle of marsh
					if numNeighborType( x, y, 'TERRAIN', etMarsh, 2 ) >= 18:
						hauntedPlots.append( pl )
						hauntedPlots.append( pl )
						continue
				elif numNeighborType( x, y, 'TERRAIN', etMarsh, 1 ) >= 3:
					hauntedPlots.append( pl )
					continue
		# choose 'Haunted Lands' from plotlist
		for p in hauntedPlots:
			if choose( chHaunted, True, False ):
				p.setPlotEffectType( efHauntedLands)
				cnt += 1
		if cnt>0: print "[MST] %i Haunted Lands placed" % ( cnt )

	# put 'Crystal Plains' on the map
	# mostly just converted from Operas 'Orbis-friendly map scripts'
	# --> http://forums.civfanatics.com/showthread.php?t=321920
	def placeCrystalPlains( self, chCrystal=25 ):
		if not bCrystalPlains: return								# no Crystal Plains -> no placement
		print "[MST] ===== FeaturePlacer:placeCrystalPlains()"
		# put 'Crystal Plains' on icy plots
		cnt = 0
		for inx in range( map.numPlots() ):
			plot = map.plotByIndex( inx )
			x, y = coordByIndex( inx )
			# check for water and mountains
			if plot.isWater() or plot.isPeak() or plot.isHills(): continue
			# check for 'Tundra'
			if plot.getTerrainType() == etTundra:
				iTemp = 1
				if plot.isRiver() == True:
					chCrystal += 5 									# rivers increase base chance
				for xx in range( x-1, x+2 ):
					for yy in range( y-1, y+2 ): 					# check surrounding plots
						pl = map.plot( xx, yy )
						if ( pl.getTerrainType()==etTundra ) or ( pl.getTerrainType()==etTaiga ):
							if pl.isRiver(): 							# surrounding plot rivers also increase chance
								chCrystal += 2
							if pl.getFeatureType() == efCrystalPlains:
								chCrystal += 5
							else: 										# only taiga or tundra
								chCrystal += 1
						elif pl.getTerrainType()==etDesert:		# desert may increase iTemp and decreases chance
							if iTemp < 3: iTemp = 3
							chCrystal -= 6
						elif pl.getTerrainType()==etPlains:		# plains may increase iTemp and decreases chance
							if iTemp < 2: iTemp = 2
							chCrystal -= 4
						else: 											# other terrains
							if iTemp < 2: iTemp = 2
							chCrystal  -= 2
				# here iTemp is used to reduce the chance of CP if the temperature is to high
				if choose( chCrystal / iTemp, True, False ):
					plot.setFeatureType( efCrystalPlains, 0 )
					cnt += 1
		if cnt>0: print "[MST] %i Crystal Plains placed" % ( cnt )

###############################################################################################################
### CLASS FeaturePlacer END
###############################################################################################################
featurePlacer = FeaturePlacer()


#########################################################################################################
########## CLASS BonusBalancer - balance starting-plot boni and place missing boni
#########################################################################################################
### The original BonusBalancer class from Warlords in CyMapGeneratorUtil.py
###   uses two tuples, which are defined within the class:
###   - resourcesToBalance, which the class tries to add for each player near the starting-plot,
###     if BonusBalancer.normalizeAddExtras() is called in normalizeAddExtras() and
###   - resourcesToEliminate, which together with the resourcesToBalance will not be placed anywhere
###     on the map, if BonusBalancer.isSkipBonus() is used within addBonusType()
### This BonusBalancer class:
###   - places all boni in the default way first
###   - eliminates all boni in resourcesToEliminate
###   - eliminates most randomly placed balanced resources
###     - but eliminates fewer balanced resources from unsettled continents (give Barbarian Nations a chance)
###   - places missing boni:
###     (boni which were not placed by addBonus(), or which were only placed once,
###      instead of the three or more expected placements by XML definition)
###      - if neccessary change from forest       to jungle, if latitude < 30
###      - if neccessary change from plains       to desert, if latitude < 45
###      - if neccessary change from grass/marsh  to tundra, if latitude > 60
###   	- if missing boni are found, eliminates a few of the most numerous resources to make room
###   - makes sure there is at least one grain or lifestock resource within city-cross range
###	  (tries to place a food resources which are already present in the area,
###      in that way different continents should have different food resources)
###     *** NOT Implemented yet ***
###   - tries to move mineralBoni [Copper,Iron,Mithril,Uranium,Silver,Coal] from flatland to hills
###   - places additional boni only if they are not already available near starting-plot
###   - tries to place those boni into the same area as starting-plot first
###   - uses different balanced resources depending on active mod
###     (only two yet: Normal and FFH - Planetfall has no strategic boni to balance)
###   - has capability to add mod-specitic resources to balance via BonusBalancer.normalizeAddExtras()
###   - has capability to add mod-specitic resources to eliminate via BonusBalancer.normalizeAddExtras()
###   - increases the range for the normalizing process by one from 6 to 8 around starting-plot
###     (may incease the range by one more, if there are not enough free plots)
###
###   Note: The wide distribution of strategic ressources means that those ressources are somewhere in
###         the vicinity of the starting-plot, but not necessarily nearer to you than to your neighbor.
###         In fact on worlds with many civilizations, they may well crop up behind your neighbor.
#########################################################################################################
# initialize(self, bBalanceOnOff=True, bMissingOnOff=True, bMineralsOnOff=True, bWideRange=False )
# normalizeAddExtras( *lResources )
# bSkip = isSkipBonus( iBonusType )
# bValid = isBonusValid( eBonus, pPlot, bIgnoreUniqueRange, bIgnoreOneArea, bIgnoreAdjacent )
# moveMinerals( lMineralsToMove=None )
# --- private ---
# eliminateBadBoni()
# reduceBalancedBoni()
# addMissingBoni()
# boniMissing, boniFound, freePlots = checkAllBoniPlaced()
# freePlots = reduceNumerousBoni( boniFound, freePlots )
# boniMissing = placeMissingBoni( boniMissing, boniFound, freePlots )
# placeBonus( plot, iBonus )
# iVariety = transformForest2Jungle( plot )
# txtMessage = transformJungleNeighbor( plot )
# txtMessage = transformTerrainNeighbor( plot, eFrom, eTo, sTxt )
# balanceStrategicBoni()
# plBoniCnt = balanceBoniAtPlot( start_plot, sprint="" )
# boniInRange = getBoniInRange( x, y, areaID, ran, player )
# freePlots = getFreePlots( x, y, areaID, ran )
# iDesire = calcNumBoniToAdd( iBonus )
#########################################################################################################
class BonusBalancer:
	# class variables
	# Note: The first bonus will be ignored about half the time,
	#       not all players will have it near their starting-plot
	resourcesToBalance   = ( 'BONUS_ALUMINUM', 'BONUS_OIL', 'BONUS_HORSE', 'BONUS_URANIUM', 'BONUS_IRON', 'BONUS_COPPER', )
	resourcesToEliminate = ('', )
	mineralsToMove       = ( 'BONUS_COPPER', 'BONUS_IRON', 'BONUS_MITHRIL', 'BONUS_SILVER', 'BONUS_GOLD', 'BONUS_URANIUM' )

	def initialize(self, bBalanceOnOff=True, bMissingOnOff=True, bMineralsOnOff=True, bWideRange=False ):
		print "[MST] ===== BonusBalancer:initialize( %r, %r, %r, %r )" % (bBalanceOnOff, bMissingOnOff, bMineralsOnOff, bWideRange)

		self.bBalance  = bBalanceOnOff
		self.bMissing  = bMissingOnOff
		self.bMinerals = bMineralsOnOff and (not bMars)
		self.spRange = 5																# max plotDistance around startingPlot
		self.iEliminate  = 50														# elimination percentage before balancing:
		self.iEliminate -= 4 * map.getWorldSize()								# smaller percentage for bigger worlds
		self.iEliminate += gc.getGame().countCivPlayersEverAlive() * 2	# and bigger percentage for more players
		self.iEliminate = min( self.iEliminate, 80 )
		self.iEliminate = max( self.iEliminate, 20 )

		# bigger worlds, less players - balanced boni spread thinner
		if bWideRange:						# spread balanced boni on a wider range around the starting plots
			self.spRange += 2
		if map.getWorldSize() > 2:		# standard+
			if gc.getGame().countCivPlayersEverAlive() < 12:
				self.spRange += 1
		if map.getWorldSize() > 3:		# large+
			if gc.getGame().countCivPlayersEverAlive() < 15:
				self.spRange += 1
		if map.getWorldSize() > 4:		# huge+
			if gc.getGame().countCivPlayersEverAlive() < 18:
				self.spRange += 1
		if map.getWorldSize() > 5:		# giant+
			if gc.getGame().countCivPlayersEverAlive() < 21:
				self.spRange += 1

		# balanced resources depending on mod
		if not self.bBalance:
			self.resourcesToBalance = ('', )
			self.resourcesToEliminate = ('', )
		elif bPfall:
			# no strategic resources for Planetfall
			self.resourcesToBalance = ('', )
			self.resourcesToEliminate = ('', )
		elif bMars:
			# very different strategic resources for Mars Now! {uranium, iron, phosphorus, titanium, gas}
			self.resourcesToBalance = ( 'BONUS_URANIUM', 'BONUS_IRON', 'BONUS_STONE', 'BONUS_IVORY', 'BONUS_WHEAT' )
			self.resourcesToEliminate = ('', )
			self.mineralsToMove       = ('', )
		elif bFFH:
			# one might also consider: BONUS_GUNPOWDER, BONUS_INCENSE, BONUS_GEMS
			self.resourcesToBalance = ( 'BONUS_MITHRIL', 'BONUS_REAGENS', 'BONUS_HORSE', 'BONUS_MANA', 'BONUS_IRON', 'BONUS_COPPER' )
			self.resourcesToEliminate = ('', )
		elif bRoM:
			self.resourcesToBalance = ( 'BONUS_BAUXITE', 'BONUS_OIL', 'BONUS_HORSE', 'BONUS_URANIUM', 'BONUS_IRON', 'BONUS_COPPER', )

		#-----------------------------------------------------
		# show which of the boni in the mod might be strategic
		def getPrereqBoni():
			aBoni = []
			aUnits = []
			for iUnit in range(gc.getNumUnitInfos()):
				type_string = gc.getUnitInfo(iUnit).getType()
				iBonus = gc.getUnitInfo(iUnit).getPrereqAndBonus()
				if iBonus>=0:
					if iBonus not in aBoni:
						aBoni.append( iBonus )
						aUnits.append( [] )
					for b in range( len(aBoni) ):
						if iBonus==aBoni[b]:
							aUnits[b].append( type_string )
				for i in range(4):
					iBonus = gc.getUnitInfo(iUnit).getPrereqOrBonuses(i)
					if iBonus>=0:
						if iBonus not in aBoni:
							aBoni.append( iBonus )
							aUnits.append( [] )
						for b in range( len(aBoni) ):
							if iBonus==aBoni[b]:
								aUnits[b].append( type_string )
			for iBuild in range(gc.getNumBuildingInfos()):
				type_string = gc.getBuildingInfo(iBuild).getType()
				iBonus = gc.getBuildingInfo(iBuild).getPrereqAndBonus()
				if iBonus>=0:
					if iBonus not in aBoni:
						aBoni.append( iBonus )
						aUnits.append( [] )
					for b in range( len(aBoni) ):
						if iBonus==aBoni[b]:
							aUnits[b].append( type_string )
			# problem with WARLORDS/VANILLA - no gc.getRouteInfo(iRoute).getPrereqBonus()
			if bBTS:
				for iRoute in range(gc.getNumRouteInfos()):
					type_string = gc.getRouteInfo(iRoute).getType()
					for i in range(4):
						iBonus = gc.getRouteInfo(iRoute).getPrereqOrBonus(i)
						if iBonus>=0 and iBonus<gc.getNumBonusInfos():
							if iBonus not in aBoni:
								aBoni.append( iBonus )
								aUnits.append( [] )
							for b in range( len(aBoni) ):
								if iBonus==aBoni[b]:
									aUnits[b].append( type_string )
				for iRoute in range(gc.getNumRouteInfos()):
					type_string = gc.getRouteInfo(iRoute).getType()
					iBonus = gc.getRouteInfo(iRoute).getPrereqBonus()
					if iBonus>=0:
						if iBonus not in aBoni:
							aBoni.append( iBonus )
							aUnits.append( [] )
						for b in range( len(aBoni) ):
							if iBonus==aBoni[b]:
								aUnits[b].append( type_string )

			sprint  = "[MST] Potentially Strategic Boni\n"
			sprint += "[MST] --------------------------\n"
			print sprint
			for b in range(len(aBoni)):
				bonus_string = gc.getBonusInfo(aBoni[b]).getType()
				bonusName = "Bonus: %s(%i) :" % ( bonus_string, len(aUnits[b]) )
				printList( aUnits[b], bonusName, 5, prefix="[MST] " )
			return
		#------------------------
		print "[MST] ###########################################"
		getPrereqBoni()
		print "[MST] ###########################################"

	# organize resourceLists, make areaList, place missing boni and balance starting-plots
	def normalizeAddExtras(self, *lResources):
		print "[MST] ===== BonusBalancer:normalizeAddExtras()"

		sprint  = "[MST] BonusBalancer " + iif( self.bBalance, "active", "deactivated") + " and "
		sprint += " MissingBoniPlacer " + iif( self.bMissing, "active", "deactivated") + " and "
		sprint += " MineralMover " + iif( self.bMinerals, "active", "deactivated")
		print sprint

		# put additional boni into resourcesToBalance; or resourcesToEliminate if preceded by a '-'
		sprint = ""
		if self.bBalance:
			# add given additional resources to balance
			if len(lResources)>0:
				newRes = list(lResources)
				print "[MST] Extra resources: %r" % ( newRes )
				balResources = list( self.resourcesToBalance )
				if balResources[0] == '': del balResources[0]
				elimResources = list( self.resourcesToEliminate )
				if elimResources[0] == '': del elimResources[0]
				for res in newRes:
					if res[0]=='-':
						if not ( res[1:] in elimResources ):
							if isBonus( res[1:] ):
								elimResources.append( res[1:] )
								removeListElement( balResources, res[1:] )
					else:
						if not ( res in balResources ):
							if isBonus( res ):
								balResources.append( res )
								removeListElement( elimResources, res )
				self.resourcesToBalance = tuple( balResources )
				self.resourcesToEliminate = tuple( elimResources )
			sprint += "[MST] Resources to balance:   %r \n" % ( self.resourcesToBalance, )
			sprint += "[MST] Resources to eliminate: %r \n" % ( self.resourcesToEliminate, )
		if self.bMinerals:
			sprint += "[MST] Minerals to move:       %r \n" % ( self.mineralsToMove, )
		print sprint

		# make lists of relevant areas
		minContinentPlots = 12
		map.recalculateAreas()
		self.areas = CvMapGeneratorUtil.getAreas()
		self.continentArea = []
		self.startArea = []
		for area in self.areas:
			if area.getNumStartingPlots()>0: self.startArea.append( area.getID() )
			if area.getNumTiles()>=minContinentPlots: self.continentArea.append( area.getID() )

		# proceed step by step
		self.cnt = 0
		mapStats.showContinents( "", minContinentPlots )			# before
		if self.bBalance:  self.eliminateBadBoni()
		if self.bBalance:  self.reduceBalancedBoni()
		if self.bMissing:  self.addMissingBoni()
#		if self.bBalance:  self.balanceFarmingBoni()					# perhaps in the next version, not sure it's needed
		if self.bBalance:  self.balanceStrategicBoni()
		if self.bMinerals: self.moveMinerals( None, False )
		mapStats.showContinents( "", minContinentPlots )			# after

	# check if bonus is within resourcesToEliminate
	# from Warlord CvMapGeneratorUtil.BonusBalancer; doesn't check resourcesToBalance
	def isSkipBonus(self, iBonusType):
#		print "[MST] ===== BonusBalancer:isSkipBonus()"
		if not self.bBalance: return False
		type_string = gc.getBonusInfo(iBonusType).getType()
		return (type_string in self.resourcesToEliminate)

	# return true, if bonus can be placed on plot
	# from Warlord CvMapGeneratorUtil.BonusBalancer
	def isBonusValid(self, eBonus, pPlot, bIgnoreUniqueRange, bIgnoreOneArea, bIgnoreAdjacent):
#		print "[MST] ===== BonusBalancer:isBonusValid()"
		iX, iY = pPlot.getX(), pPlot.getY()

		if (not bIgnoreOneArea) and gc.getBonusInfo(eBonus).isOneArea():
			if map.getNumBonuses(eBonus) > 0:
				if map.getArea(pPlot.getArea()).getNumBonuses(eBonus) == 0:
					return False
		if not bIgnoreAdjacent:
			for iI in range(DirectionTypes.NUM_DIRECTION_TYPES):
				pLoopPlot = plotDirection(iX, iY, DirectionTypes(iI))
				if not pLoopPlot.isNone():
					if (pLoopPlot.getBonusType(-1) != -1) and (pLoopPlot.getBonusType(-1) != eBonus):
						return False
		if not bIgnoreUniqueRange:
			uniqueRange = gc.getBonusInfo(eBonus).getUniqueRange()
			for iDX in range(-uniqueRange, uniqueRange+1):
				for iDY in range(-uniqueRange, uniqueRange+1):
					pLoopPlot = plotXY(iX, iY, iDX, iDY)
					if not pLoopPlot.isNone() and pLoopPlot.getBonusType(-1) == eBonus:
						return False
		return True

	# move mineral boni from flatland to neighboring hills
	# NOTE: this is usually called after balancing and may move the
	#       balanced resource up to 2 plots into the 'wrong' direction
	def moveMinerals( self, lMineralsToMove=None, bForceHills=False ):
		print "[MST] ===== BonusBalancer:moveMinerals()"

		if lMineralsToMove == None:
			lMinerals = self.mineralsToMove
		else:
			lMinerals = lMineralsToMove
		cntMove = 0
		cntHill = 0
		for inx in range( map.numPlots() ):
			plot = map.plotByIndex( inx )
			if not plot.isFlatlands(): continue
			iBonus = plot.getBonusType( -1 )
			if iBonus < 0: continue
			type_string = gc.getBonusInfo(iBonus).getType()
			if type_string in lMinerals:
				# find nearby hill
				lHills = []
				x, y = plot.getX(), plot.getY()
				dist = 2
				for dx in range( -dist, dist+1 ):
					for dy in range( -dist, dist+1 ):
						pl = plotXY( x, y, dx, dy )
						if pl.isNone(): continue
						if pl.isHills():
							neiBonus = pl.getBonusType( -1 )
							if neiBonus < 0:
								if self.isBonusValid( iBonus, pl, True, False, False ):
									lHills.append( pl )
									# 2nd chance for neighbors
									if (abs(dx)<2) and (abs(dy)<2):
										lHills.append( pl )
				# move bonus
				if len( lHills ) > 0:
					pl = chooseListElement( lHills )
					self.placeBonus( pl, iBonus )
					self.placeBonus( plot, -1 )
					cntMove += 1
				else:
					if bForceHills:
						plot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
						cntHill += 1
		print "[MST] %i boni moved, %i hills created" % ( cntMove, cntHill )

	###############
	### Helpers ###
	###############

	# eliminate boni in resourcesToEliminate
	def eliminateBadBoni( self ):
		print "[MST] ======== BonusBalancer:eliminateBadBoni()"
		if self.resourcesToEliminate[0] == '': return
		iCnt = 0
		for i in range( map.numPlots() ):
			pl = map.plotByIndex(i)
			iBonus = pl.getBonusType(-1)
			if iBonus>=0:
				type_string = gc.getBonusInfo(iBonus).getType()
				if type_string in self.resourcesToEliminate:
					self.placeBonus( pl, -1 )
					iCnt += 1
		print "[MST] Eliminated %2i of the boni to be eliminated:\n %r" % ( iCnt, self.resourcesToEliminate )

	# eliminate most balanced boni in starting-plot areas
	# - much lower elimination-chance on other continents
	# - no elimination-chance on water and small islands
	def reduceBalancedBoni(self):
		print "[MST] ======== BonusBalancer:reduceBalancedBoni()"
		iCnt = 0
		iChoice = 0
		for i in range( map.numPlots() ):
			pl = map.plotByIndex(i)
			iBonus = pl.getBonusType(-1)
			if iBonus>=0:
				type_string = gc.getBonusInfo(iBonus).getType()
				if type_string in self.resourcesToBalance:
					if bMars:
						iChoice = int( self.iEliminate / 3 )
					elif pl.getArea() in self.startArea:
						iChoice = int( self.iEliminate )
					elif pl.getArea() in self.continentArea:
						iChoice = int( self.iEliminate / 4 )
					else:
						continue
					if choose(iChoice,True,False):
						self.placeBonus( pl, -1 )
						iCnt += 1
		print "[MST] Eliminated %2i wild boni of those to be balanced (%i%s chance)\n" % ( iCnt, self.iEliminate, "%%" )

	# add boni which were not placed, but should have been
	#   also place boni which were placed only once, but should have been placed 3 or more times
	def addMissingBoni( self ):
		print "[MST] ======== BonusBalancer:addMissingBoni()"
		# check if all boni were placed
		lMissing, lFound, lFree = self.checkAllBoniPlaced()
		if len(lMissing) == 0:
			print "[MST] No missing boni found \n"
		else:
			sprint = "[MST] Missing boni found: Not all resources have been randomly placed: \n"
			for i in lMissing: sprint += "[MST] %s wasn't placed randomly \n" % (gc.getBonusInfo(i[0]).getType())
			print sprint
			# reduce numerous boni, since some other boni are missing
			lFree = self.reduceNumerousBoni( lFound, lFree )
			# try to place those missing boni now
			lMissing = self.placeMissingBoni( lMissing, lFound, lFree )
			# print warning, if there are still missing boni
			if len(lMissing)>0:
				sprint = "[MST] WARNING! - not all missing boni could be placed \n"
				for i in lMissing: sprint += "[MST] %s is still missing \n" % (gc.getBonusInfo(i[0]).getType())
				print sprint
			else:
				print "[MST] All missing boni have been placed"

	# make lists with boni and their plots
	def checkAllBoniPlaced( self ):
#		print "[MST] ======== BonusBalancer:checkAllBoniPlaced()"

		iPlayer = game.countCivPlayersAlive()
		boniMissing = []
		boniFound = []
		freePlots = []
		for i in range( gc.getNumBonusInfos() ): boniFound.append( [] )

		# make lists for placed boni and free plots
		for i in range( map.numPlots() ):
			plot = map.plotByIndex(i)
#			if plot.isWater(): continue				# ignore water boni
			iBonus = plot.getBonusType(-1)
			if iBonus<0:
				if not plot.isWater():					# no new water boni
					if not plot.isPeak():				# no boni on peaks
						freePlots.append( i )
			else:
				boniFound[iBonus].append( i )

		# make list for missing boni
		for iBonus in range( gc.getNumBonusInfos() ):
			# find missing boni
			if boniFound[iBonus] == []:
				# should bonus placed on the map, if so try to place half
				iDesiredBoni = self.calcNumBoniToAdd( iBonus )
				if iDesiredBoni > 1:
					bonusName = capWords( gc.getBonusInfo(iBonus).getType()[6:] )
					boniMissing.append( [iBonus, min(int((iDesiredBoni+1)/2),int(iPlayer/2)), bonusName] )
			# recheck single boni, if desired are >2 then place half
			elif len( boniFound[iBonus] )	== 1:
				pl = map.plotByIndex( boniFound[iBonus][0] )
				if not pl.isWater():
					iDesiredBoni = self.calcNumBoniToAdd( iBonus )
					if iDesiredBoni > 2:
						bonusName = capWords( gc.getBonusInfo(iBonus).getType()[6:] )
						boniMissing.append( [iBonus, min(int(iDesiredBoni/2),int(iPlayer/2)), bonusName] )
		return ( boniMissing, boniFound, freePlots )

	# delete some of the most placed boni on land, ignore balanced boni
	def reduceNumerousBoni(self, boniFound, freePlots):
		print "[MST] ======== BonusBalancer:reduceNumerousBoni()"
		iPlayer = game.countCivPlayersAlive()
		cnt = 0
		for i in range( len(boniFound) ):
			actBonusPlots = boniFound[i]
			if len(actBonusPlots)==0: continue
			if	map.plotByIndex(actBonusPlots[0]).isWater(): continue
			if not (i in self.resourcesToBalance):
				passes = 0
				if len(actBonusPlots) > int(1.60*iPlayer): passes = 1
				if len(actBonusPlots) > int(2.40*iPlayer): passes = 2
				if len(actBonusPlots) > int(3.20*iPlayer): passes = 3
				if len(actBonusPlots) > int(4.00*iPlayer): passes = 4
				if len(actBonusPlots) > 12: passes += 1
				if len(actBonusPlots) > 16: passes += 1
				if len(actBonusPlots) > 20: passes += 1
				cn = 0
				while passes>0:
					passes -= 1
					inx = chooseListPop( actBonusPlots )
					plot = map.plotByIndex( inx )
					self.placeBonus( plot, -1 )
					freePlots.append( inx )
					cn += 1
					cnt += 1
				# print " killed %i of %s" % ( cn, capWords( gc.getBonusInfo(i).getType()[6:] ) )
		if cnt > 0:
			print "[MST] Eliminated %2i of the most plentiful boni" % (cnt)
			randomList.shuffle( freePlots )
		return freePlots

	# place missing boni if at all possible
	def placeMissingBoni(self, boniMissing, boniFound, freePlots):
		print "[MST] ======== BonusBalancer:placeMissingBoni()"
		if len(boniMissing)==0: return boniMissing

		iPlayer = game.countCivPlayersAlive()
		randomList.shuffle( boniMissing )

		# try and place missing boni
		# using several passes, increasingly ignoring conditions on placement
		# up to changing forest to jungle, plains to desert or grass/marsh to tundra
		sprint = ""
		sprint += "[MST] %2i boni missing: %r \n" % (len(boniMissing),boniMissing)
		sprint += "[MST] %4i free Plots \n" % (len(freePlots))
		bMissing = []
		for i in range(len(boniMissing)): bMissing.append( True )

		# this is a bit of a hack, but should work anyway
		# 8 passes
		for pass_num in range(8):
			if len(boniMissing)==0: break
			if bPfall and pass_num>3: break
			bIgnoreLatitude			= True
			bIgnoreUniqueRange		= (pass_num >= 1) and (pass_num <> 4)
			bIgnoreOneArea				= (pass_num >= 2) and (pass_num <> 4) and (pass_num <> 5)
			bIgnoreAdjacent			= (pass_num >= 3) and (pass_num <> 4) and (pass_num <> 5) and (pass_num <> 6)
			bCreateTerrainFeature	= (pass_num >= 4)

			lastRound = False
			while not lastRound:
				cnt = 0
				for i in range( len(boniMissing) ):
					misBonus = boniMissing[i]
					iBonus  = misBonus[0]
					iDesire = misBonus[1]
#					sprint += "[MST] Pass %i, %s need %i more \n" % (pass_num,gc.getBonusInfo(iBonus).getType(),iDesire)
					if iDesire>0:
						for j in range( len(freePlots) ):
							inx = freePlots[j]
							bJTrans = False
							bDTrans = False
							bTTrans = False
							fp = map.plotByIndex( inx )
							if bCreateTerrainFeature:
								bIgnoreLatitude = False
								if gc.getBonusInfo(iBonus).isFeature(efJungle) or gc.getBonusInfo(iBonus).isFeatureTerrain(efJungle):
									if fp.getFeatureType()==efForest and evalLatitude(fp)<30:
										iVar = self.transformForest2Jungle(fp)
										bJTrans = True
								elif gc.getBonusInfo(iBonus).isTerrain(etDesert) or gc.getBonusInfo(iBonus).isFeatureTerrain(etDesert):
									if fp.getTerrainType()==etPlains and evalLatitude(fp)<45:
										fp.setTerrainType( etDesert, True, True )
										bDTrans = True
								elif gc.getBonusInfo(iBonus).isTerrain(etTaiga) or gc.getBonusInfo(iBonus).isFeatureTerrain(etTaiga):
									if (fp.getTerrainType()==etGrass or fp.getTerrainType()==etMarsh) and (evalLatitude(fp)>60):
										fp.setTerrainType( etTaiga, True, True )
										bTTrans = True
							if fp.canHaveBonus(iBonus, bIgnoreLatitude):
#								sprint += "[MST] plot canHaveBonus inx %i \n" % (inx)
								if self.isBonusValid(iBonus, fp, bIgnoreUniqueRange, bIgnoreOneArea, bIgnoreAdjacent):
#									sprint += "[MST] plot isBonusValid inx %i \n" % (inx)
									self.placeBonus( fp, iBonus)
									misBonus[1] -= 1
									bMissing[i] = False
									cnt += 1
									del freePlots[j]
#									sprint += "[MST] Pass %i, %s placed - %i to go \n" % ( pass_num, gc.getBonusInfo(iBonus).getType(),misBonus[1] )
									if bJTrans:
#										sprint += "[MST] Jungle created @ %i,%i \n" % (fp.getX(),fp.getY())
										self.transformJungleNeighbor( fp )
									elif bDTrans:
#										sprint += "[MST] Desert created @ %i,%i \n" % (fp.getX(),fp.getY())
										self.transformTerrainNeighbor( fp, etDesert, etPlains, 'Desert' )
									elif bTTrans:
#										sprint += "[MST] Taiga created @ %i,%i \n" % (fp.getX(),fp.getY())
										self.transformTerrainNeighbor( fp, etTaiga, iif(bMarsh,(etGrass,etMarsh),(etGrass,)), 'Taiga' )
									break
							if bJTrans:
								fp.setFeatureType(efForest,iVar)
							elif bDTrans:
								fp.setTerrainType(etPlains,True,True)
							elif bTTrans:
								fp.setTerrainType(etGrass,True,True)

				# if all desired boni are placed, the missing bonus is erased from the list
				if len(boniMissing)>0:
					r = 0
					while r<len(boniMissing):
						misBonus = boniMissing[r]
						iBonus  = misBonus[0]
						iDesire = misBonus[1]
						if iDesire == 0:
							del boniMissing[r]
							sprint += "[MST] all %s placed \n" % ( gc.getBonusInfo(iBonus).getType() )
						else:
							r += 1
					sprint += "[MST] %2i boni still missing: %r \n" % ( len(boniMissing),boniMissing )

				# if missingBoni list is empty, return with success
				if len(boniMissing)==0:
					print sprint
					return boniMissing
				# if no boni placed, try next pass or return unsuccessfully
				if cnt==0:
					lastRound = True

		bMiss = False
		for m in bMissing: bMiss = (bMiss or m)
		if not bMiss: boniMissing = []
		print sprint
		return boniMissing

	# place bonus preserving the feature variety	(in forests)
	def placeBonus(self, plot, iBonus):
#		print "[MST] ======== BonusBalancer:placeBonus()"
		eFeature = plot.getFeatureType()
		bonusInfo = gc.getBonusInfo( iBonus )
		# temp save feature and variety
		featureVariety = -1
		if eFeature>=0:
			if gc.getFeatureInfo(eFeature).getNumVarieties()>1:
				featureVariety = plot.getFeatureVariety()
				plot.setFeatureType( FeatureTypes.NO_FEATURE, -1 )
		#place bonus
		plot.setBonusType( iBonus )
		self.cnt += iif( iBonus==-1, 1, -1 )
		#restore the feature if possible
		if featureVariety>=0:
			if (bonusInfo == None) or bonusInfo.isFeature(eFeature):
				plot.setFeatureType(eFeature,featureVariety)

	# change Forest to Jungle; return variety
	def transformForest2Jungle( self, plot ):
#		print "[MST] ======== BonusBalancer:transformForest2Jungle()"
		eFeature = plot.getFeatureType()
		iVariety = plot.getFeatureVariety()
		if eFeature==efForest:
			plot.setFeatureType(efJungle,-1)
		return iVariety

	# add one more jungle plot to keep from getting lonely and strange
	def transformJungleNeighbor( self, plot ):
#		print "[MST] ======== BonusBalancer:transformJungleNeighbor()"
		x = plot.getX()
		y = plot.getY()
		sprint = ""

		pList = []
		for eCard in range( CardinalDirectionTypes.NUM_CARDINALDIRECTION_TYPES ):
			p = plotCardinalDirection( x, y, CardinalDirectionTypes(eCard) )
			if not p.isNone():
				if p.getFeatureType()==efJungle: return
				if p.getFeatureType()==efForest:
					if p.getTerrainType()==etGrass or p.getTerrainType()==etMarsh:
						if p.getBonusType(-1)<0:
							pList.append( p )
		if len(pList)>0:
			randomList.shuffle( pList )
			v = self.transformForest2Jungle( pList[0] )
			sprint += "[MST] More Jungle created @ %i,%i \n" % (pList[0].getX(),pList[0].getY())
		return sprint

	# add one more plot of same terrain to keep from getting lonely and strange
	def transformTerrainNeighbor( self, plot, eFrom, eTo, sTxt ):
#		print "[MST] ======== BonusBalancer:transformJungleNeighbor()"
		x = plot.getX()
		y = plot.getY()
		sprint = ""

		pList = []
		for eCard in range( CardinalDirectionTypes.NUM_CARDINALDIRECTION_TYPES ):
			p = plotCardinalDirection( x, y, CardinalDirectionTypes(eCard) )
			if not p.isNone():
				if p.getTerrainType() == eTo: continue
				if p.getTerrainType() == eFrom:
					if p.getFeatureType() < 0:				# no features only
						if p.getBonusType(-1) < 0:
							pList.append( p )
		if len(pList)>0:
			randomList.shuffle( pList )
			pList[0].setTerrainType( eTo, True, True )
			sprint += "[MST] More %s created @ %i,%i \n" % (	sTxt, pList[0].getX(), pList[0].getY() )
		return sprint

	'''
	# NO NEED?
	# make sure that every starting-plot has either grain or livestock resources nearby
	def balanceFarmingBoni( self ):
		print "[MST] ======== BonusBalancer:balanceFarmingBoni()"
		if bPfall: return

		iPlayer = game.countCivPlayersAlive()
		farmBoni = []
		areaFarmBoni = {}

		# determine grain and livestock boni
		for iBonus in range(gc.getNumBonusInfos()):
			iClass = gc.getBonusInfo(iBonus).getBonusClassType()
#			class_string = capWords( gc.getBonusClassInfo(iClass).getType() )
#			if (class_string=='BONUSCLASS_GRAIN') or (class_string=='BONUSCLASS_LIVESTOCK'):
			if iClass==1 or iClass==2:		# 1:Grain, 2:Livestock - there seems to be no getType() for BonusClassInfo
				type_string = capWords( gc.getBonusInfo(iBonus).getType()[6:] )
				farmBoni.append( (iBonus, type_string) )
		print "[MST] known Grain & Livestock: %r" % ( farmBoni, )
		...
	'''

	# make sure each player has at least one each of the resourcesToBalance in the vicinity
	def balanceStrategicBoni( self ):
		print "[MST] ======== BonusBalancer:balanceStrategicBoni()"
		# put boni in resourcesToBalance around starting-plots
		allBoniCnt = 0
		for i in range(gc.getMAX_CIV_PLAYERS()):
			if (gc.getPlayer(i).isAlive()):
				sprint = "[MST] PLAYER %i \n" % (i)
				start_plot = gc.getPlayer(i).getStartingPlot()
				plBoniCnt = self.balanceBoniAtPlot( start_plot, i, sprint )
				allBoniCnt += plBoniCnt
		sprint  = "[MST] Boni placed for all players: %r\n\n" % (allBoniCnt)
		sprint += "[MST] %i %s boni placed than eliminated" % ( abs(self.cnt),iif(self.cnt<0,'more','less'))
		print sprint

	# balance boni for starting-plot
	def balanceBoniAtPlot( self, start_plot, player=-1, sprint="", maxPass=3 ):
		plBoniCnt = 0
		startx, starty = start_plot.getX(), start_plot.getY()
		# two passes: within own area, ignore area
		for iPass in [1,2]:
			if iPass==2: startArea = -1
			else: startArea = start_plot.getArea()

			sPlots = self.getFreePlots(startx, starty, startArea, self.spRange)
			boniList = self.getBoniInRange( startx, starty, startArea, self.spRange)			# list of boni found

			# increase range if not enough places were found
			if len(sPlots)<=( 2 * len(self.resourcesToBalance) ):
				sPlots = self.getFreePlots(startx, starty, startArea, self.spRange+1)
				boniList = self.getBoniInRange( startx, starty, startArea, self.spRange+1 )		# list of boni found
			boniList.sort()
			sprint += "[MST] boniList: %r \n" % (boniList)
			resources_placed = []
			for pass_num in [0,1,2,3]:
				if pass_num > maxPass: break
				bIgnoreUniqueRange	= pass_num >= 1
				bIgnoreOneArea			= pass_num >= 2
				bIgnoreAdjacent		= pass_num >= 3
				for iBonus in range(gc.getNumBonusInfos()):
					type_string = gc.getBonusInfo(iBonus).getType()
					if (iBonus not in resources_placed) and (iBonus not in boniList):
						if type_string in self.resourcesToBalance:
							# ignore first bonus in list 50% of the time; don't allow further passes
							if type_string == self.resourcesToBalance[0]:
								if iPass == 2: continue
								if pass_num > 0: continue
								if choose(50, True, False): continue
							# ignore second bonus in list 33% of the time; don't allow further passes
							if len(self.resourcesToBalance) > 1:
								if type_string == self.resourcesToBalance[1]:
									if iPass == 2: continue
									if pass_num > 0: continue
									if choose(33, True, False): continue
							for pl in sPlots:
								if pl.canHaveBonus(iBonus, True):
									if self.isBonusValid(iBonus, pl, bIgnoreUniqueRange, bIgnoreOneArea, bIgnoreAdjacent):
										self.placeBonus( pl, iBonus )
										plBoniCnt += 1
										resources_placed.append(iBonus)
										pDist = plotDistance( startx, starty, pl.getX(), pl.getY() )
										break # go to the next bonus
				sprint += "[MST] passes %i,%i: resources_placed %r \n" % (iPass,pass_num,resources_placed)
		boniList = boniList + resources_placed
		boniList.sort()
		resList = [ gc.getBonusInfo(i).getType() for i in boniList ]
		if player == -1:
			txt = "Boni: %r" % (boniList)
		else:
			txt = "Boni for player %r: %r" % (player,boniList)
		sprint += sprintList( resList, txt, rows = 3, prefix = "[MST] " ) + "\n"
		sprint += "[MST] Number of boni placed: %r\n\n" % (plBoniCnt)
		return plBoniCnt

	# make list of boni already in the same area near starting-plot
	def getBoniInRange(self, x, y, areaID, ran):
#		print "[MST] ======== BonusBalancer:getBoniInRange()"
		cnt = 0
		boniInRange = []
		for dx in range(-ran,ran+1):
			for dy in range(-ran,ran+1):
				if plotDistance( x, y, x+dx, y+dy ) <= ran:
					pLoopPlot = plotXY(x, y, dx, dy)							# use build-in plotXY()
					dArea = pLoopPlot.getArea()
					if (areaID == dArea) or (areaID < 0):
						iBonus = pLoopPlot.getBonusType(-1)					# use build-in plotXY()
						if iBonus > -1:
							cnt += 1
							if (iBonus not in boniInRange):
								boniInRange.append( iBonus )
#		print "[MST] %2i boni found" % (cnt)
		return boniInRange

	# build a shuffled list of the plots in the same area near the starting plot
	def getFreePlots(self, x, y, areaID, ran ):
#		print "[MST] ======== BonusBalancer:getFreePlots()"
		plots = []
		for dx in range(-ran,ran+1):
			for dy in range(-ran,ran+1):
				if plotDistance( x, y, x+dx, y+dy ) <= ran:
					pLoopPlot = plotXY(x, y, dx, dy)							# use build-in plotXY()
					# no extra boni outside map
					if not pLoopPlot.isNone():
						dArea = pLoopPlot.getArea()
						if (areaID == dArea) or (areaID < 0):
							# no extra boni on peaks
							if not pLoopPlot.isPeak():
								# no extra boni on top of other boni
								if pLoopPlot.getBonusType(-1)<0:
									plots.append(pLoopPlot)
		randomList.shuffle( plots )
		return plots																# return list

	# calculate number of desired boni
	# - like CvMapGenerator::calculateNumBonusesToAdd(BonusTypes eBonusType) in CvMapGenerator.cpp
	def calcNumBoniToAdd(self, iBonus):
#		print "[MST] ======== BonusBalancer:calcNumBoniToAdd()"
		bonusInfo = gc.getBonusInfo( iBonus )
		if bonusInfo.getPlacementOrder()<0:	return 0
		if bonusInfo.getType() in self.resourcesToEliminate: return 0

		rand1 = chooseNumber( bonusInfo.getRandAppearance1() )
		rand2 = chooseNumber( bonusInfo.getRandAppearance2() )
		rand3 = chooseNumber( bonusInfo.getRandAppearance3() )
		rand4 = chooseNumber( bonusInfo.getRandAppearance4() )
		iBaseCount = bonusInfo.getConstAppearance() + rand1 + rand2 + rand3 + rand4

		bIgnoreLatitude = False
		iLandTiles = 0
		iNumPossible = 0
		if bonusInfo.getTilesPer() > 0:
			for i in range( iNumPlotsX*iNumPlotsY ):
				plot = map.plotByIndex(i)
				if plot.canHaveBonus( iBonus, bIgnoreLatitude ):
					iNumPossible += 1
			iLandTiles += iNumPossible / bonusInfo.getTilesPer()
		iPlayers = int( game.countCivPlayersAlive() * bonusInfo.getPercentPerPlayer() / 100 )
		iBonusCount = int( iBaseCount * (iLandTiles + iPlayers) / 100 )
		return max( 1, iBonusCount )

##########################################################################
########## CLASS BonusBalancer END
##########################################################################
bonusBalancer = BonusBalancer()


#########################################################################################################
########## CLASS RiverMaker - build additional rivers
#########################################################################################################
### Best used before addRivers().
### Otherwise the rivers are on the map, but sources and deltas sometimes look strange.
### riverLists have the form: [ riverID, [plot0,cardinalDirection0], [plot1,cardinalDirection1], ... ]
#########################################################################################################
# buildRiver( pStartPlot, bDownFlow=True, ecNext=None, ecOri=None, iThisRiverID=None, riverList=None )
# islandRivers( minIsle=6, maxIsle=50, areaID=None )
# buildRiversFromLake( lakeAreaID=None, chRiver=66, nRivers=1, minLake=1 )
# sList = outRiverList( riverList, prefix="" )
# bEdge = isEdgeDirection( self, plot, ecDir )
# bRiver =  hasRiverAtPlot( plot )
# bCorner = hasRiverAtSECorner( plot )
# bCorner = hasCoastAtSECorner( plot )
# bCorner = hasPlotTypeAtSECorner( plot, plotType )
# eCard = getBestFlowDir( plot, bDownFlow=True, bShort=False, eForbiddenList=[] )
# --- private ---
# iHeight = getPlotHeight( plot )
# fHeight = getPlotBaseHeight( plot )
# riverDirs = checkRiverEnd( plot )
# rivStart = rimRivers( x, y, distList )
#########################################################################################################
class RiverMaker:
	bMakeSourceHill = True
	bRiverStart = False
	cntHills = 0
	cntPeaks = 0
	cntLand = 0
	# make a new river beginning at the SE corner of the plot
	# basically CvMapgenerator.doRiver() with reversed flow and a list of river-plots
	# Note: While upFlow rivers can start from rivers, only downFlow rivers can end there. To produce
	#   a normal looking web of rivers, upFlow rivers should be build first. Since the default addRivers()
	#   produces only downFlow rivers, upFlow rivers should be made before or at the start of addRivers().
	def buildRiver( self, pStartPlot, bDownFlow=True, ecNext=None, ecOri=None, iThisRiverID=None, riverList=None ):
#		print "[MST] ===== RiverMaker:buildRiver()"

		self.bRiverStart = False
		# check params
		if riverList == None:
			riverList = []
			self.bRiverStart = True
		if iThisRiverID == None:
			iThisRiverID = CyMap().getNextRiverID()
			CyMap().incrementNextRiverID()
		if len(riverList)>0:
			if isList( riverList[0] ):
				riverList.insert( 0, iThisRiverID )
				riverList.insert( 1, bDownFlow )
				self.bRiverStart = True
		else:
			self.cntHills = 0
			self.cntPeaks = 0
			self.cntLand = 0
			self.bRiverStart = True
			if ecNext != None:
				riverList.append( iThisRiverID )
				riverList.append( bDownFlow )

#		print "[MST] Start River @ %i,%i - nextFlow: %5s, oriFlow: %5s -%s riverID: %i" % \
#				( pStartPlot.getX(), pStartPlot.getY(), cardinalName(ecNext), cardinalName(ecOri), iif(bDownFlow,""," Reversed Flow,"), iThisRiverID )

		# does another river already exist - we can't branch off of an existing river!
		# - actually we can, if the river starts and we go upFlow
		iOtherRiverID = pStartPlot.getRiverID()
		if (iOtherRiverID != -1) and (iOtherRiverID != iThisRiverID):
			if bDownFlow or (not self.bRiverStart):
#				print "[MST] =="> Other river already here!"
				return

		bNoDir = False
		ecBest = None
		if ecNext == None: ecNext = ecNone
		# flow direction
		ecFlow = ecNext
		if not bDownFlow:
			ecFlow = getOppositeCardinalDirection( ecNext )
		# handle each possible next direction and produce next riverPlot
		rivDirs = self.checkRiverEnd( pStartPlot, bDownFlow )				# get list of possible directions
		if ecNext == ecNorth:
			if not (ecNext in rivDirs): return
			pRiverPlot = pStartPlot
			if pRiverPlot.isNone(): return
			if pRiverPlot.isWOfRiver(): return

			pStartPlot.setRiverID( iThisRiverID )
			pRiverPlot.setWOfRiver( True, ecFlow )
			if bDownFlow:
				riverList.append( [pRiverPlot, ecFlow] )
			else:
				riverList.insert( 2, [pRiverPlot, ecFlow] )
#			print "[MST] set riverplot @ %i.%i - WestOfRiver  toward %s" % ( pRiverPlot.getX(), pRiverPlot.getY(), cardinalName(ecFlow) )
			pRiverPlot = plotCardinalDirection( pRiverPlot.getX(), pRiverPlot.getY(), ecNorth )
		elif ecNext == ecEast:
			if not (ecNext in rivDirs): return
			pRiverPlot = plotCardinalDirection( pStartPlot.getX(), pStartPlot.getY(), ecEast )
			if pRiverPlot.isNone(): return
			if pRiverPlot.isNOfRiver(): return

			pStartPlot.setRiverID( iThisRiverID )
			pRiverPlot.setNOfRiver( True, ecFlow )
			if bDownFlow:
				riverList.append( [pRiverPlot, ecFlow] )
			else:
				riverList.insert( 2, [pRiverPlot, ecFlow] )
#			print "[MST] set riverplot @ %i.%i - NorthOfRiver toward %s" % ( pRiverPlot.getX(), pRiverPlot.getY(), cardinalName(ecFlow) )
		elif ecNext == ecSouth:
			if not (ecNext in rivDirs): return
			pRiverPlot = plotCardinalDirection( pStartPlot.getX(), pStartPlot.getY(), ecSouth )
			if pRiverPlot.isNone(): return
			if pRiverPlot.isWOfRiver(): return

			pStartPlot.setRiverID( iThisRiverID )
			pRiverPlot.setWOfRiver( True, ecFlow )
			if bDownFlow:
				riverList.append( [pRiverPlot, ecFlow] )
			else:
				riverList.insert( 2, [pRiverPlot, ecFlow] )
#			print "[MST] set riverplot @ %i.%i - WestOfRiver  toward %s" % ( pRiverPlot.getX(), pRiverPlot.getY(), cardinalName(ecFlow) )
		elif ecNext == ecWest:
			if not (ecNext in rivDirs): return
			pRiverPlot = pStartPlot
			if pRiverPlot.isNone(): return
			if pRiverPlot.isNOfRiver(): return

			pStartPlot.setRiverID( iThisRiverID )
			pRiverPlot.setNOfRiver( True, ecFlow )
			if bDownFlow:
				riverList.append( [pRiverPlot, ecFlow] )
			else:
				riverList.insert( 2, [pRiverPlot, ecFlow] )
#			print "[MST] set riverplot @ %i.%i - NorthOfRiver toward %s" % ( pRiverPlot.getX(), pRiverPlot.getY(), cardinalName(ecFlow) )
			pRiverPlot = plotCardinalDirection( pRiverPlot.getX(), pRiverPlot.getY(), ecWest )
		else:
#			print "[MST] =="> Trying to find river direction; none given"
			bNoDir = True															# hack to enable water-start
			pRiverPlot = pStartPlot
			ecBest = self.getBestFlowDir( pRiverPlot, bDownFlow )		# longRiver
			if ecBest == None:
#				print "[MST] =="> No starting direction found!"
				return
		# already done?
		if pRiverPlot.isNone():
			return																	# all is well; river flows off the map
		if not bNoDir:
			if bDownFlow and self.hasCoastAtSECorner( pRiverPlot ):
				return																# all is well; river flows into ocean
			elif (not bDownFlow) and self.hasPlotTypeAtSECorner( pRiverPlot, PlotTypes.PLOT_PEAK ):
				self.cntPeaks += 1
				if self.cntPeaks >= 2:
					ch = self.cntPeaks * 100 / (self.cntPeaks + 2)		# 50,60,66,71,75 -> 50,20,06,01
					if choose( ch, True, False ):
						return														# all is well; the peak is the source
			elif (not bDownFlow) and self.hasPlotTypeAtSECorner( pRiverPlot, PlotTypes.PLOT_HILLS ):
				self.cntHills += 1
				if self.cntHills >= 3:
					ch = self.cntHills * 100 / (self.cntHills + 3)		# 50,57,62,66,70 -> 50,21,08,02
					if choose( ch, True, False ):
						return														# all is well; the hill is the source
			elif (not bDownFlow) and self.hasPlotTypeAtSECorner( pRiverPlot, PlotTypes.PLOT_LAND ):
				self.cntLand += 1
				if self.cntLand >= 6:
					ch = self.cntLand * 100 / (self.cntLand + 6)			# 50,53,57,60,62 -> 50,23,10,04,01
					if choose( ch, True, False ):
						if self.bMakeSourceHill:
							pRiverPlot.setPlotType( PlotTypes.PLOT_HILLS, True, True )
						return														# all is well; new hill is the source
		# find next direction
		if ecBest == None:
			eForbiddenList = []
			if ecOri != None: eForbiddenList.append( getOppositeCardinalDirection( ecOri ) )
			if ecNext != None: eForbiddenList.append( getOppositeCardinalDirection( ecNext ) )
			ecBest = self.getBestFlowDir( pRiverPlot, bDownFlow, True, eForbiddenList )			# shortRiver
		# build next river segment
		if ecBest != None:
			if  ecOri == None: ecOri = ecBest
			self.buildRiver( pRiverPlot, bDownFlow, ecBest, ecOri, iThisRiverID, riverList )

	# puts a river on islands, or on one island if areaID is given
	# - if they don't have one and
	# - if they have at least one inland plot
	def islandRivers( self, minIsle=6, maxIsle=50, areaID=None ):
		print "[MST] ===== RiverMaker:islandRivers()"

		# no island-rivers on Mars
		if bMars: return

		sprint = ""
		chNoHills = 66
		areas = CvMapGeneratorUtil.getAreas()
		cnt = 0
		for area in areas:
			if areaID != None:
				if not ( area.getID() == areaID ):
					continue
			aTotalPlots = area.getNumTiles()
			aRiverEdges = area.getNumRiverEdges()
			aCoastLand  = area.countCoastalLand()
			if area.isWater(): continue														# islands!
			# don't be to sure
			if aTotalPlots < (minIsle + chooseNumber( 3 ) - 1): continue			# to small
			if aTotalPlots > (maxIsle + chooseNumber( 5 ) - 2): continue			# to big
			if aRiverEdges > 0: continue														# already has river

			cnt += 1
			pList = []
			noHillsList = []
			id = area.getID()
			sprint += "\n"
			sprint += "[MST] IslandArea %i(%i) without rivers found \n" % (id,aTotalPlots)
			cntPl = 0
			cntSE = 0
			for inx in range( map.numPlots() ):
				plot = map.plotByIndex( inx )
				if id != plot.getArea(): continue											# wrong island
				cntPl += 1
				x,y = plot.getX(), plot.getY()
				if not self.hasCoastAtSECorner( plot ):									# inland-plot
					cntSE += 1
					if self.hasPlotTypeAtSECorner( plot, PlotTypes.PLOT_PEAK ):
						pList.append( plot )														# mountain-plot * 2
						pList.append( plot )
					elif self.hasPlotTypeAtSECorner( plot, PlotTypes.PLOT_HILLS ):
						pList.append( plot )														# hill-plot * 1
					else:
						noHillsList.append( plot )												# no hills/peak
			if cntPl > 0:
				sprint += "[MST] %i possible plots, %i possible corners \n" % (cntPl,cntSE)
			if len( pList ) == 0:
				sprint += "[MST] - no inland riverstart-plots with hills/peak found \n"
				if choose( chNoHills, True, False ):
					pList = noHillsList
					if len( pList ) == 0:
						sprint += "[MST] - no inland riverstart-plots found! \n"
			if len( pList ) > 0:
				plot = chooseListPop( pList )
				rList = []
				rDir = self.getBestFlowDir( plot )			# downFlow, longRiver
				if rDir != None:
					self.buildRiver( plot, True, rDir, riverList=rList )
					sprint += riverMaker.outRiverList( rList, "[MST]" )
				# chance for 2nd river depends on number of possible plots
				if choose( len(pList)-5, True, False ):
					plot = chooseListPop( pList )
					rList = []
					rDir = self.getBestFlowDir( plot )		# downFlow, longRiver
					if rDir != None:
						self.buildRiver( plot, True, rDir, riverList=rList )		# 'wrong' dir for longer river
						sprint += riverMaker.outRiverList( rList, "[MST]" )

		if (cnt == 0) and (areaID==None):
			sprint += "[MST] No smaller islands without rivers found \n"
		elif cnt==0:
			sprint += "[MST] No river created on this island\n"
		print sprint

	# build rivers from lake up
	def buildRiversFromLake( self, lakeAreaID=None, chRiver=66, nRivers=1, minLake=1 ):
#		print "[MST] ===== RiverMaker:buildRiversFromLake()"

		if lakeAreaID == None:
			print "[MST] ===== RiverMaker:buildRiversFromLake()"
			# no lake-rivers on Mars
			if bMars: return
			# build rivers from all lakes
			map.recalculateAreas()
			areas = CvMapGeneratorUtil.getAreas()
			for area in areas:
				if area.isLake():
					iAreaID = area.getID()
					self.buildRiversFromLake( iAreaID, chRiver, nRivers, minLake )
			return
		else:
			# build rivers from single lake
			area = map.getArea( lakeAreaID )
			if not area.isLake(): return													# not lake
			# don't be to sure
			if area.getNumTiles() < (minLake + chooseNumber( 3 ) - 1): return	# too small
			# make plot-list
			lPlots = getAreaPlotsXY( lakeAreaID )
			# check for old rivers
			rivList = []
			for x,y in lPlots:
				for dx in range( -1, 2 ):
					for dy in range( -1, 2 ):
						pl = plotXY( x, y, dx, dy)
						if not pl.isNone():
							rid = pl.getRiverID()
							if rid > -1:
								if (dx,dy) in [ (-1,0),(-1,1),(0,1) ]:					# W,NW,N
									if rid not in rivList:
										rivList.append( rid )
								elif (dx,dy) in [ (1,1),(1,0) ]:							# NE,E
									if pl.isNOfRiver():
										if rid not in rivList:
											rivList.append( rid )
								elif (dx,dy) in [ (-1,-1),(0,-1) ]:						# S,SW
									if pl.isWOfRiver():
										if rid not in rivList:
											rivList.append( rid )
			if len( rivList ) >= nRivers: return										# enough rivers found
			# check each plot for possible river directions
			cdirList = []
			for x,y in lPlots:
				pl = map.plot(x,y)
				if not pl.isWater():
					print "[MST] Bad Lake-Plot found!"
					continue
				# check all corners of plot
				ecDir = self.getBestFlowDir( pl, False )								# upFlow, longRiver
				if ecDir != None:
					cdirList.append( (ecDir, pl) )
				p = plotCardinalDirection( x, y, ecWest )								# West
				if not p.isNone():
					if not p.isWater():														# water-plot is checked elsewhere
						ecDir = self.getBestFlowDir( p, False )						# upFlow, longRiver
						if ecDir != None:
							cdirList.append( (ecDir, p) )
				p = plotCardinalDirection( x, y, ecNorth )							# North
				if not p.isNone():
					if not p.isWater():														# water-plot is checked elsewhere
						ecDir = self.getBestFlowDir( p, False )						# upFlow, longRiver
						if ecDir != None:
							cdirList.append( (ecDir, p) )
				p = plotDirection( x, y, DirectionTypes.DIRECTION_NORTHWEST )	# NorthWest
				if not p.isNone():
					if not p.isWater():														# water-plot has no rivers
						ecDir = self.getBestFlowDir( p, False )						# upFlow, longRiver
						if ecDir != None:
							cdirList.append( (ecDir, p) )
			# make new rivers
			sprint = ""
			newRivers = nRivers - len( rivList )
			while ( newRivers > 0 ) and ( len(cdirList) > 0 ):
				# randomly choose riverstart
				eCard, pl = chooseListPop( cdirList )
				# check if direction ends in river
				x, y = pl.getX(), pl.getY()
				p = plotCardinalDirection( x, y, CardinalDirectionTypes(eCard) )
				if not p.isNone():
					if not self.hasRiverAtSECorner( p ):
						# can build new river
						newRivers -= 1
						if choose( chRiver, True, False ):
							rList = []
							self.buildRiver( pl, False, eCard, riverList=rList )	# build upriver
							sprint += "[MST] " + "x,y %i,%i - %s \n" % (pl.getX(),pl.getY(),cardinalName(eCard))
							sprint += self.outRiverList( rList, "[MST]" )
						if area.getNumTiles() == 1:
							print sprint
							return						# only one river for mini-lakes
			if len( sprint ) > 0: print sprint

	# print riverList plots and flows
	def outRiverList( self, riverList, prefix="" ):
#		print "[MST] ===== RiverMaker:outRiverList()"
		sList = ""
		if len(riverList)<3:
			return prefix + " No River \n"
		sList += prefix + " RiverID: %i - %s \n" % (riverList[0],iif(riverList[1],"DownFlow","UpFlow"))
		sList += prefix + " --> Source:[ "
		for i in range(2,len(riverList)):
			p,e = riverList[i]
			sList += "[%i,%i - %s] " % (p.getX(),p.getY(),cardinalName(e))
		sList += "]:RiverEnd \n"
		return sList

	# check if direction leads off the map
	def isEdgeDirection( self, plot, ecDir ):
#		print "[MST] ===== RiverMaker:isEdgeDirection()"
		x, y = plot.getX(), plot.getY()
		pl = plotCardinalDirection( x, y, CardinalDirectionTypes( ecDir ) )
		if pl.isNone(): return True
		if (ecDir == ecSouth) or (ecDir == ecEast):
			dx, dy = pl.getX(), pl.getY()
			p = plotCardinalDirection( dx, dy, CardinalDirectionTypes( ecDir ) )
			if p.isNone(): return True
		return False

	# check if plot has rivers at on of its corners
	def hasRiverAtPlot( self, plot ):
#		print "[MST] ===== RiverMaker:hasRiverAtPlot()"
		if self.hasRiverAtSECorner( plot ): return True
		x, y = plot.getX(), plot.getY()
		pWPlot = plotDirection( x, y, DirectionTypes.DIRECTION_WEST )
		if not pWPlot.isNone():
			if self.hasRiverAtSECorner( pWPlot ): return True
		pNPlot = plotDirection( x, y, DirectionTypes.DIRECTION_NORTH )
		if not pNPlot.isNone():
			if self.hasRiverAtSECorner( pNPlot ): return True
		pNWPlot = plotDirection( x, y, DirectionTypes.DIRECTION_NORTHWEST )
		if not pNWPlot.isNone():
			if self.hasRiverAtSECorner( pNWPlot ): return True
		return False

	# check for river at SE-corner
	# like isRiverMask() in cvPlot.cpp
	def hasRiverAtSECorner( self, plot ):
#		print "[MST] ===== RiverMaker:hasRiverAtSECorner()"
		if plot.isNOfRiver(): return True
		if plot.isWOfRiver(): return True
		pEastPlot = plotDirection( plot.getX(), plot.getY(), DirectionTypes.DIRECTION_EAST )
		if not pEastPlot.isNone():
			if pEastPlot.isNOfRiver(): return True
		pSouthPlot = plotDirection( plot.getX(), plot.getY(), DirectionTypes.DIRECTION_SOUTH )
		if not pSouthPlot.isNone():
			if pSouthPlot.isWOfRiver(): return True
		return False

	# check for water at SE-corner
	# like hasCoastAtSECorner() in cvPlot.cpp
	def hasCoastAtSECorner( self, plot ):
#		print "[MST] ===== RiverMaker:hasCoastAtSECorner()"
		return self.hasPlotTypeAtSECorner( plot, PlotTypes.PLOT_OCEAN )

	# check for plot-type at SE-corner
	def hasPlotTypeAtSECorner( self, plot, plotType ):
#		print "[MST] ===== RiverMaker:hasPlotTypeAtSECorner()"
		if plot.getPlotType() == plotType: return True
		pAdjacentPlot = plotDirection( plot.getX(), plot.getY(), DirectionTypes.DIRECTION_EAST )
		if not pAdjacentPlot.isNone():
			if pAdjacentPlot.getPlotType() == plotType: return True
		pAdjacentPlot = plotDirection( plot.getX(), plot.getY(), DirectionTypes.DIRECTION_SOUTHEAST )
		if not pAdjacentPlot.isNone():
			if pAdjacentPlot.getPlotType() == plotType: return True
		pAdjacentPlot = plotDirection( plot.getX(), plot.getY(), DirectionTypes.DIRECTION_SOUTH )
		if not pAdjacentPlot.isNone():
			if pAdjacentPlot.getPlotType() == plotType: return True
		return False

	# get best flow-direction from SE_of_Plot
	def getBestFlowDir( self, plot, bDownFlow=True, bShort=False, eForbiddenList=[] ):
#		print "[MST] ===== RiverMaker:getBestFlowDir()"
		chRandom = 90		# chance to use the 'best' route
		chEdge =	80			# chance to hit edge deliberately
		iMin = 0
		iMax = 99999
		riverDirs = self.checkRiverEnd( plot, bDownFlow )
		iBestUpValue = iMin
		upCDir = None
		iBestDownValue = iMax
		downCDir = None
		x,y = plot.getX(), plot.getY()
		for eCard in riverDirs:
			if eCard in eForbiddenList: continue
			if self.isEdgeDirection( plot, eCard ):
				if choose( chEdge, True, False ):
					iBestUpValue = iMax
					upCDir = eCard
					iBestDownValue = iMin
					downCDir = eCard
					continue
			pl = plotCardinalDirection( x, y, CardinalDirectionTypes(eCard) )
			if not pl.isNone():
				iVal = self.getSEPlotHeight( pl )
				if iVal > iBestUpValue:
					if (iBestUpValue == iMin) or choose( chRandom, True, False ):
						iBestUpValue = iVal
						upCDir = eCard
				if iVal < iBestDownValue:
					if (iBestDownValue == iMax) or choose( chRandom, True, False ):
						iBestDownValue = iVal
						downCDir = eCard
		if bShort:
			return iif( bDownFlow, downCDir, upCDir )				# shortest way to target
		else:
			return iif( bDownFlow, upCDir, downCDir )				# longest way to target

	###############
	### Helpers ###
	###############

	# calc SE_of_Plot-height for river
	def getSEPlotHeight( self, plot ):
#		print "[MST] ======== RiverMaker:getSEPlotHeight()"
		fVal = self.getPlotHeight( plot )
		fDiv = 1.0
		x,y = plot.getX(), plot.getY()
		p1 = plotXY( x, y, 1, 0 )
		if not p1.isNone():
			fVal += self.getPlotHeight( p1 )
			fDiv += 1.0
		p2 = plotXY( x, y, 0, -1 )
		if not p2.isNone():
			fVal += self.getPlotHeight( p2 )
			fDiv += 1.0
		p3 = plotXY( x, y, 1, -1 )
		if not p3.isNone():
			fVal += self.getPlotHeight( p3 )
			fDiv += 1.0
		return fVal / fDiv

	# calc plot-height for river
	def getPlotHeight( self, plot ):
#		print "[MST] ======== RiverMaker:getPlotHeight()"
		x,y = plot.getX(), plot.getY()
		fHeight = 4.0 * self.getPlotBaseHeight( plot )						# center has quintuple weight
		i = 4
		bWater = False
		for dx in range(x-1,x+2):
			for dy in range(y-1,y+2):
				fh = self.getPlotBaseHeight( plotXY(dx,dy,0,0) )
				if fh>0:
					i += 1
					fHeight += fh
				else:
					bWater = True														# lower near water
		if bWater: i += 1
		fHeight += chooseNumber( 20 ) / 10.0									# make it fuzzy
		return 120.0 * fHeight / i

	# define base-height of plots
	def getPlotBaseHeight( self, plot ):
#		print "[MST] ======== RiverMaker:getPlotBaseHeight()"
		if plot.isWater():		return 0.0
		if plot.isFlatlands():	return 0.2
		if plot.isHills():		return 0.5
		if plot.isPeak():			return 1.0
		return 0.01

	# tests if directions from SE-corner of plot are possible
	# returns list of possible directions
	def checkRiverEnd( self, plot, bDownFlow=True ):
#		print "[MST] ======== RiverMaker:checkRiverEnd()"
		riverDirs = []
		x = plot.getX()
		y = plot.getY()
		# West
		if not plot.isWater():
			pl = plotXY( x, y, 0, -1 )				# South
			if not pl.isNone():
				if not pl.isWater():
					riverDirs.append( ecWest )
		# North
		if not plot.isWater():
			pl = plotXY( x, y, 1, 0 )				# East
			if not pl.isNone():
				if not pl.isWater():
					riverDirs.append( ecNorth )
		# East
		p1 = plotXY( x, y, 1, 0 )					# East
		if not p1.isNone():
			if not p1.isWater():
				p2 = plotXY( x, y, 1, -1 )			# SE
				if not p2.isNone():
					if not p2.isWater():
						riverDirs.append( ecEast )
		# South
		p1 = plotXY( x, y, 1, -1 )					# SE
		if not p1.isNone():
			if not p1.isWater():
				p2 = plotXY( x, y, 0, -1 )			# South
				if not p2.isNone():
					if not p2.isWater():
						riverDirs.append( ecSouth )
		# UpFlow may not end in River or Water
		if not bDownFlow:
			inx = len( riverDirs ) - 1
			while inx >= 0:
				# check if water or river is at the end
				eCard = riverDirs[inx]
				pl = plotCardinalDirection( x, y, eCard )
				if not pl.isNone():
					if self.hasRiverAtSECorner( pl ) or self.hasCoastAtSECorner( pl ):
						del riverDirs[inx]
				inx -= 1
		return riverDirs

	# find riverPlots on rim-peaks at a distance from x,y
	# if downflow - peaks have twice tha chance to be a source than hills
	# if upflow - lakes or ocean will be searched for
	def rimRivers( self, x, y, distList, bDownFlow=True ):
#		print "[MST] ======== RiverMaker:rimRivers()"
		rivStart = []							# river-starts: [ bogDir, riverPlot, eCard ]
		rPlots = []								# potential river-plots
		# get plots at distances
		for dis in distList:
			for dx in range(-dis, 1+dis):
				for dy in range(-dis, 1+dis):
					pDist = plotDistance( x, y, x+dx, y+dy )
					if pDist == dis:
						plot = plotXY( x, y, dx, dy )
						if plot.isNone(): continue
						if bDownFlow:
							# no start at SE coast
							if self.hasCoastAtSECorner( plot ): continue
							# peaks make river-start twice as probable
							if plot.isPeak():
								rPlots.append( plot )
								rPlots.append( plot )
							elif plot.isHills():
								rPlots.append( plot )
						else:
							rivDirs = self.checkRiverEnd( plot, bDownFlow )
							if ( len(rivDirs) == 1 ) or ( len(rivDirs) == 2 ) or plot.isRiver():
								rPlots.append( plot )
		# get riverPlot and eCard for river
		for pl in rPlots:
			fx = pl.getX()
			fy = pl.getY()
			bogDir = coordDirection( fx, fy, x, y )
			eCardList = getCardDirsFromDir( bogDir )
			if not bDownFlow:
				rivDirs = self.checkRiverEnd( pl, bDownFlow )
				if pl.isRiver():
					if pl.isNOfRiver():
						if pl.isWOfRiver():
							rDirs = [ ecEast, ecSouth ]
						else:
							p = plotCardinalDirection( fx, fy, ecEast )
							if not p.isNone():
								if p.isNOfRiver():
									rDirs = [ ecNorth, ecSouth ]
							p = plotCardinalDirection( fx, fy, ecSouth )
							if not p.isNone():
								if p.isWOfRiver():
									rDirs = [ ecNorth, ecEast ]
					if pl.isWOfRiver():
						if pl.isNOfRiver():
							rDirs = [ ecEast, ecSouth ]
						else:
							p = plotCardinalDirection( fx, fy, ecEast )
							if not p.isNone():
								if p.isNOfRiver():
									rDirs = [ ecWest, ecSouth ]
							p = plotCardinalDirection( fx, fy, ecSouth )
							if not p.isNone():
								if p.isWOfRiver():
									rDirs = [ ecEast, ecWest ]
					rivDirs = list( set(rivDirs) & set(rDirs) )		# no doubles in resulting list
				rivDirs = list( set(rivDirs) & set(eCardList) )		# no doubles in resulting list
				for eCard in rivDirs:
					rivStart.append( [ bogDir, pl, eCard ] )
			else:
				for eCard in eCardList:
					rivStart.append( [ bogDir, pl, eCard ] )
					if len(eCardList) == 1:
						p = plotXY( fx, fy, -1, 1 )
						if (not p.isNone()) and (not p.isWater()):
							rivStart.append( [ bogDir, p, eCard ] )
		if bDownFlow:
			# no start if a river is already there
			for i in range( len(rivStart)-1, -1, -1 ):
				if rivStart[i][1].isRiver():
					del rivStart[i]
		randomList.shuffle( rivStart )
		return rivStart

################################################################################
########## CLASS RiverMaker END
################################################################################
riverMaker = RiverMaker()


################################################################################
########## CLASS TeamStart - place team-members near to each other
################################################################################
### Uses priorities and within those places teams with most members first:
### 	1) all human team-members, team>1
###	2) at least one human in the team, team>1
###	3) no humans in the team, team>1
###	4) single-member teams
### This class uses a very simple algorithm and as a result unfortunate things
### could happen under the wrong circumstances:
### If there is no single-member team and the world is flat, the members
### of the lowest priority team may be on different sides of the world.
### Actually even with a roung world, the chances of nearby starting-plots
### for low priority teams are not very good unless there are a good number
### of single member teams.
### Note: stepDistance() is used to determine distances
################################################################################
# placeTeamsTogether( bTogether=False, bSeparated=False )
# bTeams = getTeams()
# --- private ---
# getPlotDistances()
# rangList = getBigTeam()
################################################################################
class TeamStart:
	playerList = []			# [ player, ..]
	teamDict = {}				# { teamNum : [playerNum, ..] }
	humanDict = {}				# { teamNum : iHumanity }
	playersDict = {}			# { playerNum : (plotNum, startingPlotIndex, (x, y)) }
	plotDistDict = {}			# { plotNum : [ (plotNum, distance, startingPlotIndex, (x, y)), ..] }
	startPlotDict = {}		# { plotNum : startingPlotIndex }

	# place human team-members near to each other and try to do the same for non-humans
	# if both parameters are True, starting-plots are randomized
	# if both parameters are False, return without doing anything
	def placeTeamsTogether( self, bTogether=False, bSeparated=False ):
		print "[MST] ===== TeamStart:placeTeamsTogether()"
		# housekeeping
		self.playersDict = {}
		self.playersList = []

		bTeams = self.getTeams()
		self.getPlotDistances()

		# check need
		if not bTeams:
			print "[MST] No team with more than one player. Nothing done."
			return
		elif (not bTogether) and (not bSeparated):
			print "[MST] No players are placed. Nothing done."
			return

		# check for random distribution
		if bTogether and bSeparated:
			print "[MST] All players to be randomly distributed over available starting-plots."
			plotList = []
			for pl in self.playerList:
				plotList.append( pl.getStartingPlot() )
			randomList.shuffle( plotList )
			i = 0
			for pl in self.playerList:
				pl.setStartingPlot( plotList[i], False )
				i += 1
			return

		# place teams
		print "[MST] Place teams %s" % ( iif(bTogether, "together.","separated.") )
		# get priority list
		tRangs = self.getBigTeam()
		for teamNum in tRangs:

			# find starting-plot for first team-member
			pNumList = self.teamDict[teamNum]
			# get first team-member
			playerNum = pNumList[0]
			del pNumList[0]
			# randomly choose staring-plot from remaining pool
			spNum = chooseListElement( self.startPlotDict.keys() )
			spInx = self.startPlotDict[ spNum ]
			# remove from pool
			del self.startPlotDict[ spNum ]
			# add new playerNum and starting-plot
			self.playersDict[ playerNum ] = ( spNum, spInx, coordByIndex( spInx ) )
			# more team-members
			while len( pNumList ) > 0:
				disList = self.plotDistDict[ spNum ]

				# find starting-plot for next team-member
				if bTogether:
					# find nearest possible starting-plot
					d0 = 99999
					p0 = -1
					for ospNum, dist, spInx, coords in disList:
						if ospNum in self.startPlotDict.keys():
							if dist < d0:
								d0 = dist
								p0 = ospNum
				else:
					# find farthest possible starting-plot
					d0 = 0
					p0 = -1
					for ospNum, dist, spInx, coords in disList:
						if ospNum in self.startPlotDict.keys():
							if dist > d0:
								d0 = dist
								p0 = ospNum

				# ----- ERROR handler - this shouldn't happen
				if p0 == -1:
					sprint = ""
					sprint += "[MST] ----- ERROR -----"
					sprint += "[MST] Team Start failed - No changes made to starting plots."
					sprint += "[MST] - teamDict %r" % ( self.teamDict )
					sprint += "[MST] - humanDict %r" % ( self.humanDict )
					sprint += "[MST] - plotDistDict: %r" % (self.plotDistDict)
					sprint += "[MST] - startPlotDict: %r" % (self.startPlotDict)
					sprint += "[MST] - playersDict: %r" % (self.playersDict)
					sprint += "[MST] - disList: %r" % (disList)
					sprint += "[MST] - pNumList: %r" % (pNumList)
					sprint += "[MST] -----------------"
					print sprint
					return
				# add new playerNum
				spInx = self.startPlotDict[ p0 ]
				del self.startPlotDict[ p0 ]
				oPlayerNum = pNumList[0]
				self.playersDict[ oPlayerNum ] = ( p0, spInx, coordByIndex( spInx ) )
				del pNumList[0]

		# set new starting-plots
		for playerNum in self.playersDict.keys():
			player = gc.getPlayer( playerNum )
			sPlot = map.plotByIndex( self.playersDict[ playerNum ][1] )
			player.setStartingPlot( sPlot, False )
#		self.getPlotDistances()										# debug
#		printDict( self.playersDict, " playersDict:", prefix="[MST] " )		# debug

	# create dictionary of team members and one of their humatity; teamDict, humanDict
	def getTeams( self ):
		print "[MST] ===== TeamStart:getTeams()"
		# housekeeping
		self.teamDict = {}
		self.humanDict = {}
		# get teams of players
		self.playerList = mapStats.getCivPlayerList()
		for player in self.playerList:
			playerNum = player.getID()
			teamNum = gc.getPlayer( playerNum ).getTeam()
			if not teamNum in self.teamDict.keys():
				self.teamDict[ teamNum ] = []
			self.teamDict[ teamNum ].append( playerNum )
		# get humanity of teams
		for teamNum in self.teamDict.keys():
			teamList = self.teamDict[ teamNum ]
			humanity = 0
			for playerNum in teamList:
				player = gc.getPlayer( playerNum )
				if player.isHuman():
					humanity += 1
			if humanity == len( teamList ):				# all team-members human
				humanity = 2
			elif humanity > 0:								# at least one team-member human
				humanity = 1
			self.humanDict[ teamNum ] = humanity
#		printDict( self.teamDict, "teamDict:", prefix="[MST] " )		# debug
#		printDict( self.humanDict, "humanDict:", prefix="[MST] " )		# debug

		# check for true teams
		for i in self.teamDict.keys():
			if len( self.teamDict[i] ) > 1: return True			# True if there is a team with 2 or more members
		return False

	###############
	### Helpers ###
	###############

	# create dictionarys for distances and old starting-plots;	plotDistDict, startPlotDict
	def getPlotDistances( self ):
#		print "[MST] ======== TeamStart:getPlayerDistances()"
		# housekeeping
		self.startPlotDict = {}
		self.plotDistDict = {}
		# get playerNum list
		self.playerList = mapStats.getCivPlayerList()

		# get starting-plots
		spNum = 0
		for player in self.playerList:
			pCenter = player.getStartingPlot()
			# make playerNum, startPlotDict
			self.startPlotDict[ spNum ] = indexByPlot( pCenter )
			spNum += 1

		# get starting-plot distances
		for sp in range( spNum ):
			self.plotDistDict[ sp ] = []
			# get center
			pCenter = self.startPlotDict[ sp ]
			x0, y0 = coordByIndex( pCenter )
			# get distances from center
			for osp in range( spNum ):
				otherStPlot = self.startPlotDict[ osp ]
				dx, dy = coordByIndex( otherStPlot )
				dist = stepDistance( x0, y0, dx, dy )
				self.plotDistDict[ sp ].append( ( osp, dist, otherStPlot, (dx, dy) ) )
#		printDict( self.startPlotDict, "startPlotDict:", prefix="[MST] " )		# debug
#		printDict( self.plotDistDict, "plotDistDict:", prefix="[MST] " )			# debug

	# get ranked list of teams with most members
	# 1) human team>1, 2) has human in team>1, 3) biggest team>1 4) single member teams
	def getBigTeam( self ):
#		print "[MST] ======== TeamStart:getBigTeam()"
		# get team priorities
		teamLength = []
		for teamNum in self.teamDict:
			big = 10
			if self.humanDict[ teamNum ] == 1: big = 100
			elif self.humanDict[ teamNum ] == 2: big = 1000
			if len( self.teamDict[ teamNum ] ) == 1:
				big = self.humanDict[ teamNum ]
			else:
				big += len( self.teamDict[ teamNum ] )
			teamLength.append( (big, teamNum) )
		teamLength.sort()
		teamLength.reverse()
		# return list of teams sorted by priority
		tRang = []
		for l,p in teamLength: tRang.append( p )
#		print "[MST] teamRankedList %r" % (tRang)
		return tRang

################################################################################
########## CLASS TeamStart END
################################################################################
teamStart = TeamStart()


##########################################################################################################
########## CLASS MapPrint - print maps
##########################################################################################################
# initialize()
# definePrintMap( lines, charsPerPlot, linesPerPlot, mapTitle="", mapText="",
#                 region=None, offset=None, mapLegend="" )
# printMap( bDiffDict, sMapType, sMapText="" )
# bSuccess = buildDiffMap( newDict, oldDict )
# buildAreaMap( bDiffDict=False, sText=None, region=None, areaID=None, areaDict=None )
# buildPlotMap( bDiffDict=False, sText=None, region=None, data=None )
# buildTerrainMap( bDiffDict=False, sText=None, region=None, terrainDict=None, showPlots=True )
# buildFeatureMap( bDiffDict=False, sText=None, region=None, featureDict=None, showPlots=True )
# buildBonusMap( bDiffDict=False, sText=None, region=None, bonusDict=None, showPlots=True )
# buildRiverMap( bDiffDict=False, sText=None, region=None )
# --- private ---
# sLegend = makeMapLegend( dict, addLine=None, bRiver=None, bPlayer=None )
##########################################################################################################
class MapPrint:
	# private class variables
	__lines = {}
	__charsPerPlot = 1
	__linesPerPlot = 1
	__offset       = [ 0 ]
	__mapRegion    = [0,1,0,1]
	__mapTitle     = ""
	__mapText      = ""
	__mapLegend    = ""
	__diffMaps     = {}
	manaDict       = {}				# for mana boni; for use by 'CrystallMana' module or 'WildMana' mod

	# initialize dictionaries
	def initialize( self ):
#		print "[MST] ===== MapPrint:initialize()"
		self.__diffMaps[ "PLOT" ]		= None
		self.__diffMaps[ "TERRAIN" ]	= None
		self.__diffMaps[ "FEATURE" ]	= None
		self.__diffMaps[ "BONUS" ]		= None
		self.__diffMaps[ "RIVER" ]		= None
		self.__diffMaps[ "AREAS" ]		= None

		# ---------------
		# area dictionary
		# ---------------
		self.__areaDict = {
								"Special"   : [ "$",     "Mapped Area"],
								"Ocean"     : [ " .,:;", "Ocean" ],
								"Water"     : [ "~",     "Other Water" ],
								"Continent" : [ "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "Continents" ],
								"Land"      : [ "@",     "Other Land" ]
								}

		# --------------------
		# terrain dictionaries
		# --------------------
		if bPfall:
			self.__terrainDict =	{
										etOcean      : [ ".", "Ocean"      ],
										etCoast      : [ ":", "Coast"      ],
										etShelf      : [ ",", "Shelf"      ],
										etTrench     : [ "~", "Trench"     ],
										etFlatRainy  : [ "r", "FlatRainy"  ],
										etRockyRainy : [ "R", "RockyRainy" ],
										etFlatMoist  : [ "m", "FlatMoist"  ],
										etRockyMoist : [ "M", "RockyMoist" ],
										etFlatArid   : [ "a", "FlatArid"   ],
										etRockyArid  : [ "A", "RockyArid"  ],
										etFlatPolar  : [ "p", "FlatPolar"  ],
										etRockyPolar : [ "P", "RockyPolar" ]
										}
		elif bFFH:
			self.__terrainDict =	{
										etOcean              : [ "..", "Ocean"             ],
										etCoast              : [ "::", "Coast"             ],
										etDesert             : [ "dD", "Desert"            ],
										etPlains             : [ "pP", "Plains"            ],
										etGrass              : [ "gG", "Grass"             ],
										etMarsh              : [ "mM", "Marsh"             ],
										etTaiga              : [ "tT", "Taiga"            ],
										etTundra             : [ "uU", "Tundra"              ],
										etBurningSands       : [ "bB", "BurningSands"      ],
										etBrokenLands        : [ "lL", "BrokenLands"       ],
										etFieldsOfPerdition  : [ "fF", "FieldsOfPerdition" ],
										etShallows           : [ "hH", "Shallows"          ]
										}
			if bBlackwater:    self.__terrainDict[etBlackwater]    = [ ",,", "Blackwater"    ]
			if bBlightedCoast: self.__terrainDict[etBlightedCoast] = [ ";;", "BlightedCoast" ]
		else:
			if bMarsh:
				self.__terrainDict =	{
											etOcean  : [ "..", "Ocean"  ],
											etCoast  : [ "::", "Coast"  ],
											etDesert : [ "dD", "Desert" ],
											etPlains : [ "pP", "Plains" ],
											etGrass  : [ "gG", "Grass"  ],
											etMarsh  : [ "mM", "Marsh"  ],
											etTaiga : [ "tT", "Taiga" ],
											etTundra   : [ "uU", "Tundra"   ]
											}
			else:
				self.__terrainDict =	{
											etOcean  : [ "..", "Ocean"  ],
											etCoast  : [ "::", "Coast"  ],
											etDesert : [ "dD", "Desert" ],
											etPlains : [ "pP", "Plains" ],
											etGrass  : [ "gG", "Grass"  ],
											etTaiga : [ "tT", "Taiga" ],
											etTundra   : [ "uU", "Tundra"   ]
											}
		if bOceanDeep: self.__terrainDict[ etOceanDeep ] = [ "  ", "DeepOcean"]

		# --------------------
		# feature dictionaries
		# --------------------
		if bPfall:
			self.__featureDict =	{
										efTrench       : [ "~", "Trench"       ],
										efKelp         : [ "=", "Kelp"         ],
										efIce          : [ "�", "Ice"          ],
										efSeaFungus    : [ "+", "SeaFungus"    ],
										efXenoFungus   : [ "X", "XenoFungus"   ],
										efJungle       : [ "J", "Jungle"       ],
										efHybridForest : [ "H", "HybridForest" ],
										efForest       : [ "F", "Forest"       ],
										efFallout      : [ "*", "Fallout"      ],
										efRadiation    : [ "$", "Radiation"    ]
										}
		elif bFFH:
			self.__featureDict =	{
										efIce            : [ "�", "Ice"            ],
										efFallout        : [ "*", "Fallout"        ],
										efJungle         : [ "j", "Jungle"         ],
										efForest         : [ "f", "Forest"         ],
										efOasis          : [ "o", "Oasis"          ],
										efFloodPlains    : [ "p", "FloodPlains"    ],
										efFlames         : [ '"', "Flames"         ],
										efForestAncient  : [ "F", "ForestAncient"  ],
										efForestNew      : [ "n", "ForestNew"      ],
										efForestBurnt    : [ "b", "ForestBurnt"    ],
										efTormentedSouls : [ "T", "TormentedSouls" ]
										}
		else:
			self.__featureDict =	{
										efIce          : [ "�", "Ice"          ],
										efFallout      : [ "*", "Fallout"      ],
										efJungle       : [ "j", "Jungle"       ],
										efForest       : [ "f", "Forest"       ],
										efOasis        : [ "O", "Oasis"        ],
										efFloodPlains  : [ "p", "FloodPlains"  ]
										}
		if bSwamp:          self.__featureDict[efSwamp]          = [ "w", "Swamp"          ]
		if bKelp:           self.__featureDict[efKelp]           = [ "=", "Kelp"           ]
		if bVolcano:        self.__featureDict[efVolcano]        = [ "V", "Volcano"        ]
		if bVolcanoDormant: self.__featureDict[efVolcanoDormant] = [ "v", "VolcanoDormant" ]
		if bScrub:          self.__featureDict[efScrub]          = [ "s", "Scrub"          ]
		if bCrystalPlains:  self.__featureDict[efCrystalPlains]  = [ "c", "CrystalPlains"  ]
		if bHauntedLands:   self.__featureDict[efHauntedLands]   = [ "h", "HauntedLands"   ]
		if bObsidianPlains: self.__featureDict[efObsidianPlains] = [ "P", "ObsidianPlains" ]
		if bBlizzard:       self.__featureDict[efBlizzard]       = [ "@", "Blizzard"       ]
		if bStorm:          self.__featureDict[efStorm]          = [ "@", "Storm"          ]

		# ------------------
		# bonus dictionaries
		# ------------------

		if bPfall:
			self.__bonusDict =	{
										ebBoreHoleCluster  : [ "B", "BoreHoleCluster"  ],
										ebResonanceCluster : [ "R", "ResonanceCluster" ],
										ebArtifact         : [ "A", "Artifact"         ],
										ebDimensionalGate  : [ "D", "DimensionalGate"  ],
										ebManifoldNexus    : [ "N", "ManifoldNexus"    ],
										ebMonolith         : [ "M", "Monolith"         ],
										ebTheRuins         : [ "T", "TheRuins"         ],
										ebThorium          : [ "t", "Thorium"          ],
										ebIridium          : [ "i", "Iridium"          ],
										ebFungicide        : [ "F", "Fungicide"        ],
										ebFungalGin        : [ "f", "FungalGin"        ],
										ebGrenadeFruits    : [ "G", "GrenadeFruits"    ],
										ebPholusMutagen    : [ "P", "PholusMutagen"    ]
										}
		elif bFFront:
			pass
		elif bFFH:
			self.__bonusDict =	{
										ebMana    : [ "*", "Mana"    ],
										ebReagens : [ "R", "Reagens" ],
										ebHorse   : [ "H", "Horse"   ],
										ebMithril : [ "M", "Mithril" ],
										ebIron    : [ "I", "Iron"    ],
										ebCopper  : [ "C", "Copper"  ]
										}

			self.manaDict =	{
									ebMana            : [ "@", "Mana"        ],
									ebManaMetamagic   : [ "M", "Metamagic"   ],
									ebManaEarth       : [ "E", "Earth"       ],
									ebManaWater       : [ "~", "Water"       ],
									ebManaAir         : [ "A", "Air"         ],
									ebManaFire        : [ "F", "Fire"        ],
									ebManaChaos       : [ "C", "Chaos"       ],
									ebManaEntropy     : [ "N", "Entropy"     ],
									ebManaDeath       : [ "D", "Death"       ],
									ebManaShadow      : [ "S", "Shadow"      ],
									ebManaSun         : [ "*", "Sun"         ],
									ebManaSpirit      : [ "s", "Spirit"      ],
									ebManaMind        : [ "m", "Mind"        ],
									ebManaLaw         : [ "w", "Law"         ],
									ebManaNature      : [ "n", "Nature"      ],
									ebManaLife        : [ "l", "Life"        ],
									ebManaBody        : [ "b", "Body"        ],
									ebManaEnchantment : [ "e", "Enchantment" ]
									}
			if	ebManaIce >= 0 :        self.manaDict[ebManaIce]         = [ "i", "Ice"         ]
			if ebManaDimensional >= 0: self.manaDict[ebManaDimensional] = [ "d", "Dimensional" ]
			if ebManaCreation >= 0:    self.manaDict[ebManaCreation]    = [ "c", "Creation"    ]
			if ebManaForce >= 0:       self.manaDict[ebManaForce]       = [ "f", "Force"       ]
			if ebManaRefined >= 0:     self.manaDict[ebManaRefined]     = [ "r", "Refined"     ]

		else:
			self.__bonusDict =	{
										ebAluminum : [ "A", "Aluminum" ],
										ebCopper   : [ "C", "Copper"   ],
										ebIron     : [ "I", "Iron"     ],
										ebOil      : [ "O", "Oil"      ],
										ebUranium  : [ "U", "Uranium"  ],
										ebHorse    : [ "h", "Horse"    ]
										}
			if bRoM: self.__bonusDict[ ebBauxite ] = [ "B", "Bauxite" ]

	# define class variables
	def definePrintMap( self, lines, charsPerPlot, linesPerPlot, mapTitle="", mapText="", region=None, offset=None, mapLegend="" ):
#		print "[MST] ===== MapPrint:definePrintMap()"
		self.__lines        = lines
		self.__charsPerPlot = charsPerPlot
		self.__linesPerPlot = linesPerPlot
		self.__mapLegend    = mapLegend
		if mapTitle == None:
			self.__mapTitle = "The Map"
		else:
			self.__mapTitle = mapTitle
		if mapText == None:
			self.__mapText = ""
		else:
			self.__mapText = mapText
		if offset == None:
			self.__offset = []
			for i in range( linesPerPlot ): self.__offset.append( i*1000 )
		else:
			self.__offset = offset
		if region == None:
			if self.__mapRegion == None:
				self.__mapRegion	= [0, iNumPlotsX-1, 0, iNumPlotsY-1]
		else:
			self.__mapRegion = region
#		printList( self.__mapRegion, "definePrintMap.mapRegion:", prefix="[MST] " )

	# print the map as defined by class-variables
	# if diffList is given, a second map with the differences is printed
	def printMap( self, bDiffDict, sMapType, sMapText="" ):
#		print "[MST] ===== MapPrint:printMap()"
		print "[MST] ####################################################################### MapScriptTools:MapPrint ###"
		printList( self.__mapRegion, self.__mapTitle, prefix="[MST] " )
		# print title
		sprint = "[MST] "
		if sMapType == "DIFF":
			sprint += sMapText
		else:
			if sMapText == "":
				sprint += self.__mapTitle + " { " + self.__mapText + " } -  X-Wrap: %r, Y-Wrap: %r" % (map.isWrapX(),map.isWrapY())
			else:
				sprint += self.__mapTitle + " " + sMapText + "  -  X-Wrap: %r, Y-Wrap: %r" % (map.isWrapX(),map.isWrapY())
			sprint += "\n " + "="*(len(sprint)-1)
		print sprint
		# prepare
		x0, x1, y0, y1	= self.__mapRegion
		numX = x1 - x0 + 1
		numY = y1 - y0 + 1
		preLine = 5
		mapTop = space(preLine) + "-"*(self.__charsPerPlot*(x1-x0+1)) + "+ \n"
		xLine  = space(preLine) + space(self.__charsPerPlot*(x1-x0+1) + ((x1-x0)/10) + 20 )

		for i in range( ((x1-x0)/10) + 1 ):
			off = preLine + 1 + i*10*self.__charsPerPlot
			mapTop = strInsert( mapTop, off+i-1, "+" )
			if self.__charsPerPlot==1:
				xLine = strExchange( xLine, off+i-2, (iif(i>=10,"%03i"," %02i")%(i*10+x0)) )
			else:
				xLine = strExchange( xLine, off+i-1, (iif(i>=10,"%03i","|%02i")%(i*10+x0)) )
		xLine = xLine[0:len(mapTop)-self.__charsPerPlot-3]

		# adjust for vertical wrap
		if self.__linesPerPlot > 1:
			if self.__lines[ self.__offset[self.__linesPerPlot-1] ] != None:
				if map.isWrapY():
					self.__lines[ self.__offset[self.__linesPerPlot-1]+numY ] = self.__lines[ self.__offset[self.__linesPerPlot-1] ]
				self.__lines[ self.__offset[self.__linesPerPlot-1] ] = None
		# list-print map
		lprint = []

		if map.isWrapY():
			try:
				lprint.append( "     |%s| \n" % (self.__lines[ self.__offset[self.__linesPerPlot-1]+numY ]) )
			except:
				pass
				# print "%r \n [ self.__linesPerPlot,numY ]%i,%i \n -----" % (lprint,self.__linesPerPlot,numY)

		for y in range(y1,y0-1,-1):
			xx, yy = normalizeXY( 0, y )
			if map.isWrapY() and ( not map.isWrapX() ):
				lprint.append( "%3i: |%s|:%3i\n" % (yy, self.__lines[ self.__offset[0] + y ], yy) )
			else:
				pl = map.plot(0, yy)
				soff = self.__offset[0] + y
				slin = self.__lines[ soff ]
				ev = evalLatitude( pl )
				lprint.append( "%3i: |%s|:%3i - %3i \n" % ( yy, slin, yy, ev ) )
			for i in range( 1,len(self.__offset) ):
				if self.__lines[ self.__offset[i]+y ] != None:
					lprint.append( "     |%s| \n" % (self.__lines[ self.__offset[i]+y ]) )

		# insert grid
		for i in range( len(lprint) ):
			n = (numX - 1) / 10
			while n>0:
				off = preLine + 1 + n*10*self.__charsPerPlot
				lprint[i] = strInsert( lprint[i], off, "|" )
				n -= 1
		lprint.insert( 0, mapTop )

		if self.__charsPerPlot > 1:
			latLine = xLine + iif(x1>99, "%03i| ", "%02i | ")
		else:
			latLine = xLine + iif(x1>99, "%03i", "%02i ")

		if map.isWrapY() and ( not map.isWrapX() ):
			latLine += "\n"
		else:
			latLine += "    Latitude\n"

		lprint.insert( 0, latLine % x1 )
		lprint.append( mapTop )
		lprint.append( latLine % x1 )
		# string-print map
		sprint = ""
		for s in lprint: sprint += s
		print sprint
		# print legend
		if self.__mapLegend!="":
			print self.__mapLegend
		print "[MST] ####################################################################### MapScriptTools:MapPrint ###"

		# check if difference-map is wanted
		if bDiffDict:
			# produce difference-map if possible and prepare for next call
			actMap = self.__lines.copy()
			actMap[ 'REGION' ] = self.__mapRegion
			actMap[ 'TITLE' ] = self.__mapTitle
			actMap[ 'TEXT' ] = self.__mapText
			# check if we actually have a previous map with the same region
			if (self.__diffMaps[ sMapType ] != None) and (self.__diffMaps[ sMapType ]['REGION'] == actMap['REGION']):
				# build difference map and print
				oldMap = self.__diffMaps[ sMapType ].copy()
				dprint = self.buildDiffMap( actMap, oldMap )
				if dprint:
					self.printMap( False, "DIFF" )

			# now store actual map for the next time and exit
			self.__diffMaps[ sMapType ] = actMap
			self.__diffMaps[ sMapType ][ 'REGION' ] = actMap[ 'REGION' ]
			self.__diffMaps[ sMapType ][ 'TITLE' ] = actMap[ 'TITLE' ]
			self.__diffMaps[ sMapType ][ 'TEXT' ] = actMap[ 'TEXT' ]

	# build new dictionary with differences of two maps; return True for success
	# - note that this only builds the difference-map and does not print it
	def buildDiffMap( self, newDict, oldDict ):
#		print "[MST] ===== MapPrint:buildDiffMap()"

		# check type
		if newDict[ 'TITLE' ] != oldDict[ 'TITLE' ]:
			print "[MST] Error! Different map type: %r - %r (new,old)" % ( newDict['TITLE'], oldDict['TITLE'] )
			return False
		# check region
		if newDict[ 'REGION' ] != oldDict[ 'REGION' ]:
			print "[MST] Error! Different region: %r - %r (new,old)" % ( newDict['REGION'], oldDict['REGION'] )
			return False
		# check length
		if len(newDict) != len(oldDict):
			print "[MST] Error! Different dict-length: %i, %i (new,old)" % ( len(newDict), len(oldDict) )
			return False

		# make title
		diffTitle  = "Difference Map:     -     X-Wrap: %r, Y-Wrap: %r \n" % (map.isWrapX(),map.isWrapY())
		diffTitle += space(4) + oldDict[ 'TITLE' ] + ": " + oldDict[ 'TEXT' ] + "\n"
		diffTitle += space(4) + newDict[ 'TITLE' ] + ": " + newDict[ 'TEXT' ] + "\n\n"
		# build difference dictionary
		dDiff = {}
		oldKeys = oldDict.keys()
		for lin in newDict.keys():
			if lin == 'TEXT': continue
			if lin == 'TITLE': continue
			if lin == 'REGION': continue

			# line not found in old map
			if lin not in oldKeys:
				print "[MST] Error! Key: %r is only in new dict" % ( lin )
				printDict( newDict[lin], "New Map", prefix="[MST] " )
				printDict( oldDict[lin], "Old Map", prefix="[MST] " )
				return False
			# both lines are empty
			if (newDict[lin] == None) and (oldDict[lin] == None):
				dDiff[lin] = None
				continue
			# one of the lines is empty
			if (newDict[lin] == None) or (oldDict[lin] == None):
				print "[MST] Error! Key: %r is None in one dict" % ( lin )
				printDict( newDict[lin], "New Map", prefix="[MST] " )
				printDict( oldDict[lin], "Old Map", prefix="[MST] " )
				return False
			# lines have different length
			if len(newDict[lin]) != len(oldDict[lin]):
				print "[MST] Error! Different line-length in dicts. Line: %r (new %i, old %i)" % ( lin,len(newDict[lin]),len(oldDict[lin]) )
				printDict( newDict[lin], "New Map", prefix="[MST] " )
				printDict( oldDict[lin], "Old Map", prefix="[MST] " )
				return False

			# make map
			# - may need adjustment for maps which play with more lines and chars per plot
			s = ""
			if self.__linesPerPlot > 1:
				# if more than 1 line (rivermap), we build only changed new plots
				for i in range( len( newDict[lin] ) ):
					s += iif( newDict[lin][i]==oldDict[lin][i], " ", newDict[lin][i] )
			else:
				# if one line (not rivermap), we use first char only and build diffs
				for i in range( len( newDict[lin] )/self.__charsPerPlot ):
					sNew = newDict[lin][self.__charsPerPlot * i]
					sOld = oldDict[lin][self.__charsPerPlot * i]
					if sNew == sOld:
						s += " ,,"
					else:
						s += " " + sOld + sNew
			dDiff[lin] = s
		# define map parameters
		cPP = iif( self.__linesPerPlot > 1, self.__charsPerPlot, 3 )	# may have to change
		lPP = iif( self.__linesPerPlot > 1, self.__linesPerPlot, 1 )	# redundant for now
		self.definePrintMap( dDiff, cPP, lPP, mapTitle=diffTitle, mapText = "" )
		return True

	# print areas, 1*1 chars/plot
	# build the map by filling the map-dictionary and defining the other class-variables
	# use default area-dictionary or a user supplied dictionary
	# - note that areas are not recalculated
	def buildAreaMap( self, bDiffDict=False, sText=None, region=None, areaID=None, areaDict=None ):
#		print "[MST] ===== MapPrint:buildAreaMap()"

		# get title
		self.__mapTitle = "Area Map"
		if sText == None:
			self.__mapText = ""
		else:
			self.__mapText = sText

		# get terrain dictionary
		if areaDict == None:
			dAreas = self.__areaDict
		else:
			dAreas = areaDict

		# make legend
		plotLine1 = [ "A-Z,a-z Continents", "_.,:; Ocean" ]
		self.__mapLegend  = self.makeMapLegend( dAreas, plotLine1 )

		# get printRange
		if region == None:
			x0, x1, y0, y1	= [0, iNumPlotsX-1, 0, iNumPlotsY-1]
		else:
			x0, x1, y0, y1	= region

		# empty map-dictionary and set map-parameter
		self.__lines = {}
		self.__charsPerPlot = 1
		self.__linesPerPlot = 1
		self.__offset = [ 0 ]
		self.__mapRegion = [x0, x1, y0, y1]

		# get all areas
		areaList = CvMapGeneratorUtil.getAreas()
		aList = [ (area.getNumTiles(), area.getID(), area.isWater()) for area in areaList ]
		aList.sort()
		aList.reverse()
#		printList( aList, "Areas:", 3, prefix="[MST] " )
		# build areaID-dictionary
		aDict = {}
		waterCnt = 0
		landCnt = 0
		actID = iif( type(areaID)==type(0), areaID, -1 )
		for tiles, id, bWater in aList:
			if id == actID:
				c = dAreas["Special"][0]
			elif bWater:
				if waterCnt < len( dAreas["Ocean"][0] ):
					c = dAreas["Ocean"][0][waterCnt]
					waterCnt += 1
				else:
					c = dAreas["Water"][0]
			else:
				if landCnt < len( dAreas["Continent"][0] ):
					c = dAreas["Continent"][0][landCnt]
					landCnt += 1
				else:
					c = dAreas["Land"][0]
			aDict[ id ] = c
			aList = aDict.keys()

		# build map-dictionary
		for y in range(y0,y1+1):
			linPlots = ""
			for x in range(x0,x1+1):
				xx, yy = normalizeXY(x, y)
				pl = map.plot(xx, yy)
				id = pl.getArea()
				if id in aList:
					linPlots += aDict[ id ]
				else:
					linPlots += "?"									# something is wrong - unknown area
			# place lines into dictionary
			self.__lines[ self.__offset[0] + y ] = linPlots
		# print the feature-map
		self.printMap( bDiffDict, "AREAS" )

	# print plots, may use data list, 1*1 chars/plot
	# build the map by filling the map-dictionary and defining the other class-variables
	def buildPlotMap( self, bDiffDict=False, sText=None, region=None, data=None ):
#		print "[MST] ===== MapPrint:buildPlotMap()"

		# get title
		self.__mapTitle = "Plot Map"
		if sText == None:
			self.__mapText = ""
		else:
			self.__mapText = sText

		# make legend
		self.__mapLegend  = "      . Water   - Flatlands   h Hills   M Peak \n"

		# get printRange
		if region == None:
			# no region --> full map
			x0, x1, y0, y1	= [0, iNumPlotsX-1, 0, iNumPlotsY-1]
		elif type( region ) == type( 0 ):
			# areaID --> find region for area
			x0, x1, y0, y1 = getRegion( region )
		else:
			x0, x1, y0, y1	= region

		# empty map-dictionary and set map-parameter
		self.__lines = {}
		self.__charsPerPlot = 1
		self.__linesPerPlot = 1
		self.__offset = [ 0 ]
		self.__mapRegion = [x0, x1, y0, y1]

		# build map-dictionary
		if data == None:
			for y in range(y0,y1+1):
				linPlots = ""
				for x in range(x0,x1+1):
					xx, yy = normalizeXY(x, y)
					pl = map.plot(xx, yy)
					if	pl.isWater():
						linPlots += "."
						continue
					elif pl.isFlatlands():
						linPlots += "-"
					elif pl.isHills():
						linPlots += "h"
					elif pl.isPeak():
						linPlots += "M"
					else:
						linPlots += "X"				# something is wrong
				# place lines into dictionary; we don't want the flow from y==0 anyway
				self.__lines[ self.__offset[0]+y ] = linPlots
		else:
			for y in range(y0,y1+1):
				linPlots = ""
				for x in range(x0,x1+1):
					xx, yy = normalizeXY(x, y)
					i = map.plotNum(xx,yy)
					if	data[i] == PlotTypes.PLOT_OCEAN:
						linPlots += "."
						continue
					elif data[i] == PlotTypes.PLOT_LAND:
						linPlots += "-"
					elif data[i] == PlotTypes.PLOT_HILLS:
						linPlots += "h"
					elif data[i] == PlotTypes.PLOT_PEAK:
						linPlots += "M"
					else:
						linPlots += "X"				# something is wrong
				# place lines into dictionary; we don't want the flow from y==0 anyway
				self.__lines[ self.__offset[0]+y ] = linPlots
		# print the plot-map
		self.printMap( bDiffDict, "PLOT" )

	# print terrain, 1*1 chars/plot
	# build the map by filling the map-dictionary and defining the other class-variables
	# use default terrain-dictionaries or a user supplied dictionary
	def buildTerrainMap( self, bDiffDict=False, sText=None, region=None, terrainDict=None, showPlots=True ):
#		print "[MST] ===== MapPrint:buildTerrainMap()"

		# get title
		if DEBUG: printDict( self.__terrainDict, prefix="[MST] " )
		self.__mapTitle = "Terrain Map"
		if sText == None:
			self.__mapText = ""
		else:
			self.__mapText = sText

		# get terrain dictionary
		if terrainDict == None:
			dTerrains = self.__terrainDict
		else:
			dTerrains = terrainDict
		knownTerrains = dTerrains.keys()

		# make legend
		plotLine = [ "_ Flatland", "- Hills", "^ Peak" ]
		self.__mapLegend  = self.makeMapLegend( dTerrains, iif( showPlots, plotLine, None ) )

		# get printRange
		if region == None:
			# no region --> full map
			x0, x1, y0, y1	= [0, iNumPlotsX-1, 0, iNumPlotsY-1]
		elif type( region ) == type( 0 ):
			# areaID --> find region for area
			x0, x1, y0, y1 = getRegion( region )
		else:
			x0, x1, y0, y1	= region

		# empty map-dictionary and set map-parameter
		self.__lines = {}
		self.__charsPerPlot = 1
		self.__linesPerPlot = 1
		self.__offset = [ 0 ]
		self.__mapRegion = [x0, x1, y0, y1]

		# build map-dictionary
		sprint = ""
#		print "[MST] Terrains: %r \n %r" % (knownTerrains,dTerrains)
		for y in range(y0,y1+1):
			linPlots = ""
			for x in range(x0,x1+1):
				xx, yy = normalizeXY(x, y)
				pl = map.plot(xx, yy)
				ter = pl.getTerrainType()
				if ter == -1:											# no terrain!
					if showPlots:
						if pl.isPeak():
							linPlots += "^"
						elif pl.isWater():
							linPlots += " "
						elif pl.isHills():
							linPlots += "-"
						else:
							linPlots += "_"
					else:
						linPlots += " "
				elif ter in knownTerrains:
					if len( dTerrains[ter][0] ) > 1:
						if pl.isHills():
							linPlots += dTerrains[ter][0][1]
						else:
							linPlots += dTerrains[ter][0][0]
					else:
						linPlots += dTerrains[ter][0]
				else:
					linPlots += "?"									# something is wrong - unknown terrain
					sprint += "[MST] Unknown Terrain @ %i,%i - %i.%r \n" % (xx, yy, ter, gc.getTerrainInfo(ter).getType())
					sprint += "[MST] - known Terrains: %r \n" % (dTerrain)
			# place lines into dictionary
			self.__lines[ self.__offset[0]+y ] = linPlots
		# print errors, if any
		if sprint != "": print sprint
		# print the terrain-map
		self.printMap( bDiffDict, "TERRAIN" )

	# print features, 1*1 chars/plot
	# build the map by filling the map-dictionary and defining the other class-variables
	# use default feature-dictionaries or a user supplied dictionary
	def buildFeatureMap( self, bDiffDict=False, sText=None, region=None, featureDict=None, showPlots=True ):
#		print "[MST] ===== MapPrint:buildFeatureMap()"

		# get title
		if DEBUG: printDict( self.__featureDict, prefix="[MST] " )
		self.__mapTitle = "Feature Map"
		if sText == None:
			self.__mapText = ""
		else:
			self.__mapText = sText

		# get terrain dictionary
		if featureDict == None:
			dFeatures = self.__featureDict
		else:
			dFeatures = featureDict
		knownFeatures = dFeatures.keys()

		# make legend
		plotLine = [ "_ Flatland", "- Hills", "^ Peak" ]
		self.__mapLegend  = self.makeMapLegend( dFeatures, iif( showPlots, plotLine, None ) )

		# get printRange
		if region == None:
			# no region --> full map
			x0, x1, y0, y1	= [0, iNumPlotsX-1, 0, iNumPlotsY-1]
		elif type( region ) == type( 0 ):
			# areaID --> find region for area
			x0, x1, y0, y1 = getRegion( region )
		else:
			x0, x1, y0, y1	= region

		# empty map-dictionary and set map-parameter
		self.__lines = {}
		self.__charsPerPlot = 1
		self.__linesPerPlot = 1
		self.__offset = [ 0 ]
		self.__mapRegion = [x0, x1, y0, y1]

		# build map-dictionary
		sprint = ""
#		print "[MST] Features: %r \n %r" % (knownFeatures,dFeatures)
		for y in range(y0,y1+1):
			linPlots = ""
			for x in range(x0,x1+1):
				xx, yy = normalizeXY(x, y)
				pl = map.plot(xx, yy)
				feat = pl.getFeatureType()
				if feat == -1:											# no feature!
					if showPlots:
						if pl.isPeak():
							linPlots += "^"
						elif pl.isWater():
							linPlots += " "
						elif pl.isHills():
							linPlots += "-"
						else:
							linPlots += "_"
					else:
						linPlots += " "
				elif feat in knownFeatures:
					if len( dFeatures[feat][0] ) > 1:
						if pl.isHills():
							linPlots += dFeatures[feat][0][1]
						else:
							linPlots += dFeatures[feat][0][0]
					else:
						linPlots += dFeatures[feat][0]
				else:
					linPlots += "?"									# something is wrong - unknown feature
					sprint += "[MST] Unknown Feature @ %i,%i - %i.%r \n" % (xx, yy, feat, gc.getFeatureInfo(feat).getType())
					sprint += "[MST] - known Features: %r \n" % (dFeatures)
			# place lines into dictionary
			self.__lines[ self.__offset[0]+y ] = linPlots
		# print errors, if any
		if sprint != "": print sprint
		# print the feature-map
		self.printMap( bDiffDict, "FEATURE" )

	# print boni, 1*1 chars/plot
	# build the map by filling the map-dictionary and defining the other class-variables
	# use default bonus-dictionaries or a user supplied dictionary
	def buildBonusMap( self, bDiffDict=False, sText=None, region=None, bonusDict=None, showPlots=True ):
#		print "[MST] ===== MapPrint:buildBonusMap()"

		# get title
		if DEBUG: printDict( self.__bonusDict, prefix="[MST] " )
		self.__mapTitle = "Bonus Map"
		if sText == None:
			self.__mapText = ""
		else:
			self.__mapText = sText

		# get terrain dictionary
		if bonusDict == None:
			dBonus = self.__bonusDict
		else:
			dBonus = bonusDict
		knownBoni = dBonus.keys()

		# make legend
		plotLine1 = [ "_ Flatland", "- Hills", "^ Peak", "# StartingPlot" ]
		plotLine2 = [ "# StartingPlot" ]
		self.__mapLegend  = self.makeMapLegend( dBonus, iif( showPlots, plotLine1, plotLine2 ) )

		# get printRange
		if region == None:
			# no region --> full map
			x0, x1, y0, y1	= [0, iNumPlotsX-1, 0, iNumPlotsY-1]
		elif type( region ) == type( 0 ):
			# areaID --> find region for area
			x0, x1, y0, y1 = getRegion( region )
		else:
			x0, x1, y0, y1	= region

		# empty map-dictionary and set map-parameter
		self.__lines = {}
		self.__charsPerPlot = 1
		self.__linesPerPlot = 1
		self.__offset = [ 0 ]
		self.__mapRegion = [x0, x1, y0, y1]

		# get starting-plots
		startPlotList = []
		playerList = mapStats.getCivPlayerList()
		for player in playerList:
			plot = player.getStartingPlot()
			startPlotList.append( indexByPlot(plot) )

		# build map-dictionary
		sprint = ""
#		print "[MST] Boni: %r \n %r" % (knownBoni,dBonus)
		for y in range(y0,y1+1):
			linPlots = ""
			for x in range(x0,x1+1):
				xx, yy = normalizeXY(x, y)
				pl = map.plot(xx, yy)
				inx = indexByPlot( pl )
				bon = pl.getBonusType(-1)
				if inx in startPlotList:
					linPlots += "#"
				elif bon == -1:											# no bonus!
					if showPlots:
						if pl.isPeak():
							linPlots += "^"
						elif pl.isWater():
							linPlots += " "
						elif pl.isHills():
							linPlots += "-"
						else:
							linPlots += "_"
					else:
						linPlots += " "
				elif bon in knownBoni:
					if len( dBonus[bon][0] ) > 1:
						if pl.isHills():
							linPlots += dBonus[bon][0][1]
						else:
							linPlots += dBonus[bon][0][0]
					else:
						linPlots += dBonus[bon][0][0]
				else:
					linPlots += "?"									# unknown bonus
#					sprint += "[MST] Unknown Bonus @ %i,%i - %i.%r \n" % (xx, yy, bon, gc.getFeatureInfo(bon).getType())
#					sprint += "[MST] - known Boni: %r \n" % (dBonus)
			# place lines into dictionary
			self.__lines[ self.__offset[0]+y ] = linPlots
		# print errors, if any
		if sprint != "": print sprint
		# print the feature-map
		self.printMap( bDiffDict, "BONUS" )

	# print plots, rivers and starting-plots, 3*2 chars/plot
	# build the map by filling the map-dictionary and defining the other class-variables
	def buildRiverMap( self, bDiffDict=False, sText=None, region=None ):
#		print "[MST] ===== MapPrint:buildRiverMap()"

		# get title
		self.__mapTitle = "River Map"
		if sText == None:
			self.__mapText = ""
		else:
			self.__mapText = sText

		# make legend
		self.__mapLegend  = "      . Water   - Flatlands   h Hills   M Peak \n"
		self.__mapLegend += "      nn  StartingPlot for player nn  \n"
		self.__mapLegend += "      v,  <<,  ^,  >>   rivers with flow-direction"

		# get printRange
		# get printRange
		if region == None:
			# no region --> full map
			x0, x1, y0, y1	= [0, iNumPlotsX-1, 0, iNumPlotsY-1]
		elif type( region ) == type( 0 ):
			# areaID --> find region for area
			x0, x1, y0, y1 = getRegion( region )
		else:
			x0, x1, y0, y1	= region
		numX = x1 - x0 + 1
		numY = y1 - y0 + 1

		# empty map-dictionary and set map-parameter
		self.__lines = {}
		self.__charsPerPlot = 3
		self.__linesPerPlot = 2
		self.__offset = [ 0, 1000 ]
		self.__mapRegion = [x0, x1, y0, y1]

		# build map-dictionary
		for y in range(y0,y1+1):
			linPlots = ""
			linFlows = ""
			for x in range(x0,x1+1):
				xx,yy = normalizeXY( x, y )
				pl = map.plot(xx,yy)
				if	pl.isWater():
					linPlots += ".. "
					linFlows += ".. "
					continue
				elif pl.isFlatlands():
					linPlots += "--"
				elif pl.isHills():
					linPlots += "hh"
				elif pl.isPeak():
					linPlots += "MM"
				else:
					linPlots += "XX"				# something is wrong
				if pl.isNOfRiver() or pl.isWOfRiver():
					if pl.isNOfRiver():
						if pl.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_WEST:
							linFlows += "<< "
						else:
							linFlows += ">> "
					else:
						linFlows += "   "
					if pl.isWOfRiver():
						if pl.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_NORTH:
							linPlots += "^"
						else:
							linPlots += "v"
					else:
						linPlots += " "
				else:
					linPlots += " "
					linFlows += "   "
			# place lines into dictionary; we don't want the flow from y==0 anyway
			self.__lines[ self.__offset[0]+y ] = linPlots
			self.__lines[ self.__offset[1]+y ] = linFlows
		# adjust for vertical wrap
		if map.isWrapY():
			self.__lines[ self.__offset[1]+numY ] = self.__lines[ self.__offset[1] ]
		self.__lines[ self.__offset[1] ] = None

		# get starting-plots if available
		startingPlots = []
		for p in mapStats.getCivPlayerList():
			player = gc.getPlayer( p.getID() )
			startingPlots.append( [p.getID(), player.getStartingPlot().getX(), player.getStartingPlot().getY()] )
#		print "[MST] Starting-Plots: %r" % ( startingPlots )
		if len( startingPlots ) > 0:
			# if starting-plots already exist: put them on the map
			for n,x,y in startingPlots:
				if (x != -1) and (y != -1):
					lin = self.__lines[ self.__offset[0]+y ]
					off = self.__charsPerPlot*x
					self.__lines[ self.__offset[0]+y ] = strExchange( lin, off, ("%02i"%(n)) )
		# print the river-map
		self.printMap( bDiffDict, "RIVER" )

	###############
	### Helpers ###
	###############

	# make map-legend string from dictionary
	def makeMapLegend( self, dict, addLine=None, bRiver=None, bPlayer=None ):
#		print "[MST] ======== MapPrint:makeMapLegend()"
		offset = 6
		iMax = 4

		vList = dict.values()
		vList.sort( key = lambda test: len(test[1]) )
		vList.reverse()
		nTab = len( vList[0][1] )
		aTab = 0
		if not (addLine == None):
			aList = addLine
			aList.sort( key = lambda test: len(test) )
			aTab = len( aList[0] )
		nTab = max( aTab, nTab ) + 6
		if nTab > 20: iMax -= 1
		if nTab < 15: iMax += 1

		tList = [ offset, offset+nTab, offset+2*nTab, offset+3*nTab, offset+4*nTab, offset+5*nTab, offset+6*nTab ]
		sLegend = [ space(offset+(iMax+1)*nTab), space(offset+(iMax+1)*nTab), space(offset+(iMax+1)*nTab) ]
		vList.sort( key = lambda test: test[1] )

		sprint = ""
		sLine = [ "", "", "" ]
		bLeg = [ False, False, False ]
		row = [ 0, 0, 0 ]
		for leg in vList:
			# single key
			if len( leg[0] ) == 1:
				abr = leg[0]
				if abr == " ": abr = 'blank'
				sLegend[2] = strExchange( sLegend[2], tList[row[2]], abr )
				sLegend[2] = strExchange( sLegend[2], tList[row[2]]+1+len(abr), leg[1] )
				row[2] += 1
				bLeg[2] = True
				if row[2] > iMax:
					sLine[2] += sLegend[2] + "\n"
					sLegend[2] = space(offset+5*nTab)
					row[2] = 0
			# extra key for hills
			elif len( leg[0] ) == 2:
				for i in [0,1]:
					# same extra key - show only once
					if leg[0][0] == leg[0][1]:
						if i == 0:
							abr = leg[0][0]
							if abr == " ": abr = 'blank'
							sLegend[2] = strExchange( sLegend[2], tList[row[2]], abr )
							sLegend[2] = strExchange( sLegend[2], tList[row[2]]+1+len(abr), leg[1] )
							row[2] += 1
							bLeg[2] = True
							if row[2] > iMax:
								sLine[2] += sLegend[2] + "\n"
								sLegend[2] = space(offset+(iMax+1)*nTab)
								row[2] = 0
					# show all keys and values
					else:
						abr = leg[0][i]
						if abr == " ": abr = 'blank'
						sLegend[i] = strExchange( sLegend[i], tList[row[i]], abr )
						sLegend[i] = strExchange( sLegend[i], tList[row[i]]+1+len(abr), leg[1] )
						row[i] += 1
						bLeg[i] = True
						if row[i] > iMax:
							if i == 1:
								sLine[i] += strExchange( sLegend[i], tList[iMax+1], "... on Hills \n" )
							else:
								sLine[i] += sLegend[i] + "\n"
							sLegend[i] = space(offset+(iMax+1)*nTab)
							row[i] = 0
		# close all lines
		for i in [0,1,2]:
			if row[i] > 0:
				if i == 1:
					sLine[i] += strExchange( sLegend[i], tList[iMax+1], "... on Hills \n" )
				else:
					sLine[i] += sLegend[i] + "\n"
		# consolidate lines
		for i in [0,1,2]:
			if bLeg[i]:
				sprint += sLine[i]
		# add special line
		if not (addLine == None):
			sNew = space(offset+(iMax+1)*nTab)
			cnt = 0
			for s in addLine:
				sNew = strExchange( sNew, tList[cnt], s )
				cnt += 1
			sprint += sNew + "\n"
		if not (bRiver == None):
			sprint += space( offset ) + "v,  <<,  ^,  >>   rivers with flow-direction \n"
		if not (bPlayer == None):
			sprint += space( offset ) + "nn  StartingPlot for player nn \n"
		return sprint

#############################################################################################################
########## CLASS MapPrint END
#############################################################################################################
mapPrint = MapPrint()


##############################################################
########## CLASS MapStats - print statistics about map and mod
##############################################################
# mapStatistics()
# tPlotStats = statPlotCount( txt=None )
# showContinents( txt=None, minPlots=3, bWater=False )
# sTechs = getTechList( prefix = "", bFullVersion=True )
# listPlayers = getCivPlayerList()
# sprint = sprintActiveCivs( showTeams=False, showTraits=False, showHumans=False )
# --- private ---
# sBoniTable = doBonusChart( boni )
# andTech, orTech = getTechPrereqLists( iTech )
# techLevel = getTechLevel( iTech )
# listManaTypes = getManaLists()
# sCivs = getCivilizationList()
# sTraits = getTraitList( player )
# sCultVict = getCultureVictoryConditions()
##############################################################
class MapStats:

	techLevels = {}

	# print statistics about the map and the mod
	def mapStatistics( self, bFullVersion=True ):
#		print "[MST] ===== MapStats:mapStatistics()"

		sprint = ""
		# Get available Plot/Terrain/Feature/Bonus/Improvement
		stats_plo  = []
		stats_ter  = []
		stats_feat = []
		stats_bon  = []
		stats_imp  = []
		for plo in range(4):
			stats_plo.append( 0 )
		for ter in range(gc.getNumTerrainInfos()):
			stats_ter.append( 0 )
		for feat in range(gc.getNumFeatureInfos()):
			stats_feat.append( 0 )
		for bon in range(gc.getNumBonusInfos()):
			stats_bon.append( 0 )
		for imp in range(gc.getNumImprovementInfos()):
			stats_imp.append( 0 )

		if bFullVersion:
			iPlayer = game.countCivPlayersAlive()
			# Count stats for each plot
			for i in range( map.numPlots() ):
				pl = map.plotByIndex(i)
				# get infos
				gpiPlot			= pl.getPlotType()
				gpiTerrain		= pl.getTerrainType()
				gpiBonus			= pl.getBonusType(-1)
				gpiFeature		= pl.getFeatureType()
				gpiImprovement	= pl.getImprovementType()
				# add up
				if gpiPlot == PlotTypes.PLOT_OCEAN:
					stats_plo[0] += 1
				elif gpiPlot == PlotTypes.PLOT_LAND:
					stats_plo[1] += 1
				elif gpiPlot == PlotTypes.PLOT_HILLS:
					stats_plo[2] += 1
				elif gpiPlot == PlotTypes.PLOT_PEAK:
					stats_plo[3] += 1
				if gpiTerrain>(-1):     stats_ter[gpiTerrain] += 1
				if gpiFeature>(-1):     stats_feat[gpiFeature] += 1
				if gpiBonus>(-1):       stats_bon[gpiBonus] += 1
				if gpiImprovement>(-1): stats_imp[gpiImprovement] += 1

			# Display Plot-Statistics
			print "[MST] ####################################################################### MapScriptTools:MapStats ###"
			# the short version
			self.statPlotCount( "" )

			# show continents
			self.showContinents( " Continents and Islands of the World", 2, True )

			# Display available Plots
			sprint += "[MST]   Stats of available Terrain, Features etc. \n"
			sprint += "[MST]   ----------------------------------------- \n"
			sprint += "[MST]   %i Width x %i Height = %i Plots,  %2i Players" % (iNumPlotsX, iNumPlotsY, map.numPlots(), iPlayers ) + "\n\n"
			f1 = (stats_plo[0]*100.0) / map.numPlots()
			f2 = (stats_plo[1]*100.0) / map.numPlots()
			f3 = (stats_plo[2]*100.0) / map.numPlots()
			f4 = (stats_plo[3]*100.0) / map.numPlots()
			f5 = (stats_plo[1]+stats_plo[2])*100.0 / map.numPlots()
			sprint += "[MST]   Plots: #0 - PLOT_OCEAN ( %4i )  = %4.1f%s Water" 		% (stats_plo[0], f1, '%%') + "\n"
			sprint += "[MST]   Plots: #1 - PLOT_LAND  ( %4i )  = %4.1f%s Land   }" 	% (stats_plo[1], f2, '%%') + "\n"
			sprint += "[MST]   Plots: #2 - PLOT_HILLS ( %4i )  = %4.1f%s Hills  }= %4.1f%s Usable Land" % (stats_plo[2], f3, '%%', f5, '%%') + "\n"
			sprint += "[MST]   Plots: #3 - PLOT_PEAK  ( %4i )  = %4.1f%s Peaks" 		% (stats_plo[3], f4, '%%') + "\n\n"

		# Display available Mod-Terrain
		for ter in range(gc.getNumTerrainInfos()):
			type_string = gc.getTerrainInfo(ter).getType()
			sprint += "[MST]   Terrain: #%2i - %s ( %i ) \n" % (ter, type_string, stats_ter[ter])
		sprint += "\n"

		# Display available Mod-Features
		for feat in range(gc.getNumFeatureInfos()):
			type_string = gc.getFeatureInfo(feat).getType()
			sprint += "[MST]   Feature: #%2i - %s ( %i ) \n" % (feat, type_string, stats_feat[feat])
		sprint += "\n"

		# Display available Mod-Resources
		sprint += self.doBonusChart( stats_bon )
		sprint += "\n"

		# Display available Mod-Improvements
		for imp in range(gc.getNumImprovementInfos()):
			type_string = gc.getImprovementInfo(imp).getType()

			try:
				bUnique = gc.getImprovementInfo(imp).isUnique()
			except:
				bUnique = False

			sUnique = "-"
			if bUnique: sUnique = "*"
			sprint += "[MST]   Improvement: #%3i %s %s ( %i ) \n" % (imp, sUnique, type_string, stats_imp[imp])
		sprint += "\n"

		# Display available Mod-Technologies
		sprint += self.getTechList( "[MST]", bFullVersion )

		# Display available Mod-Civilizations
		sprint += self.getCivilizationList( "[MST]" )

		if bFullVersion:
			# Display active Civilizations
			sprint += self.sprintActiveCivs( bTeams, True, True )		# show teams, traits and humanity

		# Culture Victory
		sprint += "\n[MST] " + self.getCultureVictoryConditions()
		print sprint
		print "[MST] ####################################################################### MapScriptTools:MapStats ###"
		return sprint

	# count all plots and print stats
	def statPlotCount( self, txt=None ):
#		print "[MST] ===== MapStats:statPlotCount()"
		# print title
		sprint = ""
		if txt == None:
			sprint += "[MST] ####################################################################### MapScriptTools:MapStats ### \n\n"
		elif txt	!= "":
			sprint += "[MST] " + txt + "\n " + "-"*len(txt) + "\n"
		# count plots
		nOcean = 0
		nLand = 0
		nHills = 0
		nPeak = 0
		for i in range( map.numPlots() ):
			p = map.plotByIndex(i)
			if p.isWater():
				nOcean += 1
			elif p.isFlatlands():
				nLand += 1
			elif p.isHills():
				nHills += 1
			elif p.isPeak():
				nPeak += 1
		aPlots = (nOcean, nLand, nHills, nPeak)
		# calc stats
		iAllLand = aPlots[1] + aPlots[2] + aPlots[3]
		if iAllLand==0: return None								# call after generatePlotTypes()
		fHills   = 100.0 * aPlots[2] / iAllLand
		fPeak    = 100.0 * aPlots[3] / iAllLand
		fAllLand = 100.0 * iAllLand / map.numPlots()
		# print stats
		sprint += "[MST] Plot-Stats: %i ( Water:%i, Flat:%i, Hills:%i, Peaks:%i )\n" % (map.numPlots(), aPlots[0], aPlots[1], aPlots[2], aPlots[3])
		sprint += "[MST] AllLand: %i, Hills/Land: %5.2f, Peaks/Land: %5.2f, Land/AllPlots: %5.2f\n" % ( iAllLand, fHills, fPeak, fAllLand )
		sprint += "[MST] " + '-'*73 + "\n"
		print sprint
		return ( aPlots, fHills, fPeak )

	# show stats of land areas; by default without smallest islands/lakes
	def showContinents( self, txt=None, minPlots=3, bWater=False ):
#		print "[MST] ===== MapStats:showContinents()"
		sprint = ""
		aList = []
		wList = []

		# print title
		if txt == None:
			sprint += "[MST] ####################################################################### MapScriptTools:MapStats ### \n\n"
		elif txt	!= "":
			sprint += "[MST] " + txt + "\n\n"
		areas = CvMapGeneratorUtil.getAreas()
		areaValue = {}
		sprint += "[MST] Continent Areas \n"
		sprint += "[MST] --------------- \n"
		sprint += "[MST] Area ID , Total Plots, Area Value, Start-Plots, Best Yield, Boni Total/Unique, River Edges, Coastal Land\n"
		for area in areas:
			aTotalPlots = area.getNumTiles()
			if aTotalPlots < minPlots:
				continue
			if area.isWater():
				sLake = "Ocean"
				if area.isLake(): sLake = "Lake"
				wList.append( "[MST] %8i,     %4i   - Water: %s\n" % ( area.getID(), aTotalPlots, sLake ) )
			else:
				aStartPlots = area.getNumStartingPlots()
				aBestYield  = area.calculateTotalBestNatureYield()
				aTotalBoni  = area.getNumTotalBonuses()
				aUniqueBoni = area.countNumUniqueBonusTypes()
				aRiverEdges = area.getNumRiverEdges()
				aCoastLand  = area.countCoastalLand()
				areaValue[area.getID()] = aBestYield + aRiverEdges + 3 * aUniqueBoni + aCoastLand
				aList.append( "[MST] %8i,     %4i   ,  %5i    ,    %4i    ,   %5i   ,       %3i / %3i  ,    %4i    ,    %4i\n" % \
								( area.getID(), aTotalPlots, areaValue[area.getID()], aStartPlots, aBestYield, aTotalBoni, aUniqueBoni, aRiverEdges, aCoastLand ) )
		#print aList[1][18:26]
		aList.sort( key = lambda test: test[18:26] )
		aList.reverse()
		wList.sort( key = lambda test: test[18:26] )
		wList.reverse()
		for s in aList: sprint += s
		if bWater:
			for s in wList: sprint += s
		print sprint

	# get list of techs
	def getTechList( self, prefix = "", bTechLevels=True ):
#		print "[MST] ======== MapStats:getTechLists()"
		sTechs = ""
		for tech in range(gc.getNumTechInfos()):
			tech_string = gc.getTechInfo(tech).getType()
			aTech, oTech = self.getTechPrereqLists( tech )
			andTech = []
			for i in range( len(aTech) ):
				andTech.append( gc.getTechInfo( aTech[i] ).getType()[5:] )
			orTech = []
			for i in range( len(oTech) ):
				orTech.append( gc.getTechInfo( oTech[i] ).getType()[5:] )
			if bTechLevels:
				sTechs += prefix + "   Technology: #%3i - %25s(%2i) - " % (tech,tech_string[5:], self.getTechLevel(tech))
			else:
				sTechs += prefix + "   Technology: #%3i - %25s - " % ( tech,tech_string[5:] )
			start1 = True
			for i in range( len(andTech) ):
				if not start1:
					sTechs += "AND "
				else:
					start1 = False
				sTechs += capWords(andTech[i]) + " "
			if len(andTech)>0 and len(orTech)>1:
				sTechs += "AND ( "
			elif len(andTech)>0 and len(orTech)>0:
				sTechs += "AND "
			start2 = True
			for i in range( len(orTech) ):
				if not start2:
					sTechs += "OR "
				else:
					start2 = False
				sTechs += capWords(orTech[i]) + " "
			if len(andTech)>0 and len(orTech)>1:
				sTechs += ") "
			sTechs += "\n"
		sTechs += "\n"
		return sTechs

	# get list of active players
	def getCivPlayerList( self ):
#		print "[MST] ===== MapStats:getCivPlayerList()"
		listPlayers = [ gc.getPlayer( i ) for i in range( gc.getMAX_CIV_PLAYERS() )
										  if gc.getPlayer(i).isAlive() ]
		return listPlayers

	# Display active Civilizations
	def sprintActiveCivs( self, showTeams=False, showTraits=False, showHumans=False ):
		sprint = ""
		for p in self.getCivPlayerList():
			player = gc.getPlayer( p.getID() )
			teamNum = player.getTeam()
			tList = self.getTraitList( player )
			plot = player.getStartingPlot()
			x,y = plot.getX(), plot.getY()
			civ = p.getName()
			if showHumans: civ = iif(player.isHuman(), '{Human}' + civ, civ)
			if showTeams:
				sprint += "[MST]   Active Civilization: #%2i [%2i] - @ %3i,%2i - %s [%s]\n" % ( p.getID(), teamNum, x, y, civ, p.getCivilizationDescription(0) )
			else:
				sprint += "[MST]   Active Civilization: #%2i - @ %3i,%2i - %s [%s]\n" % ( p.getID(), x, y, civ, p.getCivilizationDescription(0) )
			if showTraits: sprint += "[MST]%s( %s ) \n" % ( space( iif(showTeams, 49, 44) ), tList )
		return sprint

	###############
	### Helpers ###
	###############

	# paint a chart for boni
	def doBonusChart( self, boni ):
#		print "[MST] ======== MapStats:doBonusChart()"
		bs  =   "[MST]   |Bonus#| Bonus                      |Count |Health|Happy |Strat|Yields  |"
		if bFFH: bs += "Mana  |"
		bs += "Revealed Tech, Era"

		bs += "\n[MST]   +------+----------------------------+------+------+------+-----+--------|"
		if bFFH:	bs += "------+"
		bs += "------------------"

		# get list of mana-types depending on mod
		manaElem, manaNec, manaDiv, manaAlt, manaMeta = self.getManaLists()

		nBoni = nHeal = nHap = nMana = 0
		for bon in range(gc.getNumBonusInfos()):
			type_string = gc.getBonusInfo(bon).getType()
			if gc.getBonusInfo(bon).isTerrain( etCoast ) or gc.getBonusInfo(bon).isTerrain( etOcean ):
				type_string = "*" + type_string
			elif gc.getBonusInfo(bon).isFeatureTerrain( etCoast ) or gc.getBonusInfo(bon).isFeatureTerrain( etOcean ):
				type_string = "*" + type_string
			else:
				if bPfall:
					if gc.getBonusInfo(bon).isTerrain( etShelf ) or gc.getBonusInfo(bon).isFeatureTerrain( etShelf ):
						type_string = "*" + type_string
					else:
						type_string = " " + type_string
				else:
					type_string = " " + type_string

			sHeal = sHap = ".."
			sStrat = "."
			nY0 = nY1 = nY2 = 0
			sMana = "...."

			iHealth    = gc.getBonusInfo(bon).getHealth()
			if iHealth<>0: sHeal = "%2i" % iHealth

			iHappiness = gc.getBonusInfo(bon).getHappiness()
			if iHappiness<>0: sHap = "%2i" % iHappiness

			if bFFH:
				if type_string.find("_MANA")>-1:
					nMana += boni[bon]
					if type_string[6:] in manaElem:   sMana = "Elem"
					elif type_string[6:] in manaNec:  sMana = "Nec "
					elif type_string[6:] in manaDiv:  sMana = "Div "
					elif type_string[6:] in manaAlt:  sMana = "Alt "
					elif type_string[6:] in manaMeta: sMana = "Meta"
					else: sMana = "Raw "

			if (iHealth<=0) and (iHappiness<=0) and (type_string.find("_MANA")<0):
				sStrat = "X"

			sYield0 = "%2i" % (gc.getBonusInfo(bon).getYieldChange(0))
			sYield1 = "%2i" % (gc.getBonusInfo(bon).getYieldChange(1))
			sYield2 = "%2i" % (gc.getBonusInfo(bon).getYieldChange(2))

			iTech = gc.getBonusInfo(bon).getTechReveal()
			if iTech in range( gc.getNumTechInfos() ):
				sTech = gc.getTechInfo(iTech).getType()
				sTech = sTech.replace("_", " ")
				sTech = capWords( sTech[5:] )
				iTechEra = gc.getTechInfo(iTech).getEra()
				sTechEra = gc.getEraInfo(iTechEra).getType()
				sTechEra = sTechEra.replace("_", " ")
				sTechEra = capWords( sTechEra[4:] )

			bs += "\n[MST]   | %3i  | %-27s| %4i |..%2s..|..%2s..|..%1s..|%2s,%2s,%2s|" % (bon,type_string,boni[bon],sHeal,sHap,sStrat,sYield0,sYield1,sYield2)
			if bFFH: bs += ".%4s.|" % (sMana)
			if iTech>0: bs += " " + sTech + ", " + sTechEra
			nBoni += boni[bon]
			nHeal += boni[bon] * iHealth
			nHap  += boni[bon] * iHappiness

		bs += "\n[MST]   +------+----------------------------+------+------+------+-----+--------+"
		if bFFH:	bs += "------+"
		bs += "------------------"

		bs += "\n[MST]   |      |                            | %4i | %4i | %4i |     |        |" % (nBoni, nHeal, nHap)
		if bFFH:	bs += " %4i |" % (nMana)
		return bs + "\n"

	# get technology prerequisites
	def getTechPrereqLists( self, iTech ):
#		print "[MST] ======== MapStats:getTechPrereqs()"
		andTech = []
		orTech = []
		if iTech in range( gc.getNumTechInfos() ):
			i = 0
			while gc.getTechInfo(iTech).getPrereqAndTechs(i) in range( gc.getNumTechInfos() ):
				andTech.append( gc.getTechInfo(iTech).getPrereqAndTechs(i) )
				i += 1
			i = 0
			while gc.getTechInfo(iTech).getPrereqOrTechs(i) in range( gc.getNumTechInfos() ):
				orTech.append( gc.getTechInfo(iTech).getPrereqOrTechs(i) )
				i += 1
		return andTech, orTech

	# get technology level
	def getTechLevel( self, iTech ):
#		print "[MST] ======== MapStats:getTechLevel( %i )" % (iTech)
		techLevel = -1
		if self.techLevels.get(iTech,None) == None:
			if iTech in range( gc.getNumTechInfos() ):
				techLevel = 0
				andTech, orTech = self.getTechPrereqLists( iTech )
				if (len(andTech) > 0) or (len(orTech) > 0):
					aLevel = []
					amax = 0
					for a in range( len(andTech) ):
						aLevel.append( self.getTechLevel(andTech[a]) )
						amax = max( aLevel )
					oLevel = []
					omin = 0
					for o in range( len(orTech) ):
						oLevel.append( self.getTechLevel(orTech[o]) )
						omin = min( oLevel )
					techLevel = max( amax, omin ) + 1
				self.techLevels[iTech] = techLevel
		else:
			techLevel = self.techLevels[iTech]

#		print "[MST] Tech# %3i - Level: %2i" % (iTech, techLevel)
		return techLevel

	# get list of mana-types
	def getManaLists( self ):
#		print "[MST] ======== MapStats:getManaLists()"
		if bRoD:														# same as FFH
			manaElem = [ "MANA_EARTH", "MANA_WATER", "MANA_AIR", "MANA_FIRE" ]
			manaNec  = [ "MANA_DEATH", "MANA_CHAOS", "MANA_ENTROPY", "MANA_SHADOW" ]
			manaDiv  = [ "MANA_LIFE", "MANA_SPIRIT", "MANA_MIND", "MANA_SUN", "MANA_LAW" ]
			manaAlt  = [ "MANA_NATURE", "MANA_ENCHANTMENT", "MANA_BODY" ]
			manaMeta = [ "MANA_METAMAGIC", "MANA_ICE" ]
		elif bFF:
			manaElem = [ "MANA_EARTH", "MANA_WATER", "MANA_AIR", "MANA_FIRE", "MANA_ICE" ]
			manaNec  = [ "MANA_DEATH", "MANA_CHAOS", "MANA_ENTROPY", "MANA_SHADOW", "MANA_DIMENSIONAL" ]
			manaDiv  = [ "MANA_LIFE", "MANA_SPIRIT", "MANA_MIND", "MANA_SUN", "MANA_LAW" ]
			manaAlt  = [ "MANA_NATURE", "MANA_ENCHANTMENT", "MANA_BODY", "MANA_CREATION", "MANA_FORCE" ]
			manaMeta = [ "MANA_METAMAGIC" ]
		elif bWMana:
			manaElem = [ "MANA_EARTH", "MANA_WATER", "MANA_AIR", "MANA_FIRE", "MANA_ICE" ]
			manaNec  = [ "MANA_DEATH", "MANA_CHAOS", "MANA_ENTROPY", "MANA_SHADOW" ]
			manaDiv  = [ "MANA_LIFE", "MANA_SPIRIT", "MANA_MIND", "MANA_SUN", "MANA_LAW" ]
			manaAlt  = [ "MANA_NATURE", "MANA_ENCHANTMENT", "MANA_BODY", "MANA_CREATION", "MANA_FORCE" ]
			manaMeta = [ "MANA_METAMAGIC" ]
		elif bOrbis:
			manaElem = [ "MANA_EARTH", "MANA_WATER", "MANA_AIR", "MANA_FIRE" ]
			manaNec  = [ "MANA_DEATH", "MANA_CHAOS", "MANA_ENTROPY", "MANA_SHADOW" ]
			manaDiv  = [ "MANA_SPIRIT", "MANA_MIND", "MANA_SUN", "MANA_LAW" ]
			manaAlt  = [ "MANA_NATURE", "MANA_ENCHANTMENT", "MANA_BODY", "MANA_LIFE", "MANA_DIMENSIONAL" ]
			manaMeta = [ "MANA_METAMAGIC", "MANA_ICE", "REFINED_MANA" ]
		else:
			manaElem = [ "MANA_EARTH", "MANA_WATER", "MANA_AIR", "MANA_FIRE" ]
			manaNec  = [ "MANA_DEATH", "MANA_CHAOS", "MANA_ENTROPY", "MANA_SHADOW" ]
			manaDiv  = [ "MANA_LIFE", "MANA_SPIRIT", "MANA_MIND", "MANA_SUN", "MANA_LAW" ]
			manaAlt  = [ "MANA_NATURE", "MANA_ENCHANTMENT", "MANA_BODY" ]
			manaMeta = [ "MANA_METAMAGIC", "MANA_ICE" ]
		return [ manaElem, manaNec, manaDiv, manaAlt, manaMeta ]

	# get list of all possible civilizations
	def getCivilizationList( self, prefix = "" ):
#		print "[MST] ======== MapStats:getCivilizationList()"
		sCivs = ""
		for civ in range(gc.getNumCivilizationInfos()):
			civ_string = gc.getCivilizationInfo(civ).getType()
			sCivs += prefix + "   Civilization: #%2i - %s \n" % (civ,civ_string)
		sCivs += "\n"
		return sCivs

	# get list of active leader traits
	def getTraitList( self, player ):
#		print "[MST] ======== MapStats:getTraitList()"
		nTraits = gc.getNumTraitInfos()
		sTraits = ""
		pInfo = gc.getLeaderHeadInfo( player.getLeaderType() )
		bFirst = True
		for i in range( nTraits ):
			if ( pInfo.hasTrait(i) ):
				if bFirst:
					bFirst = False
				else:
					sTraits += ", "
				sTraits += gc.getTraitInfo(i).getType()[6:].capitalize()
		return sTraits

	# get culture victory conditions
	def getCultureVictoryConditions( self ):
#		print "[MST] ======== MapStats:getCultureVictoryConditions()"
		# VictoryInfo
		vic = -1
		for i in range(gc.getNumVictoryInfos()):
			if gc.getVictoryInfo(i).getType() == "VICTORY_CULTURAL":
				vic = i
				break
		if vic < 0:
			return "  Culture Victory: None \n"
		# num cities:
		iNum = gc.getVictoryInfo(vic).getNumCultureCities()
		# cultureType
		iCult = gc.getVictoryInfo(vic).getCityCulture()
		# cultureTypeName
		sCult = gc.getCultureLevelInfo(iCult).getType()[13:].capitalize()
		# cultureWin
		iSpeed = gc.getGame().getGameSpeedType()
		iCultWin = gc.getCultureLevelInfo(iCult).getSpeedThreshold(iSpeed)
		sCultVict = "  Culture Victory: %i Cities with %s ( %i ) Culture \n" % (iNum, sCult, iCultWin )
		return sCultVict

################################################################################
########## CLASS MapStats END
################################################################################
mapStats = MapStats()


################################################################################
########## CLASS MST_TerrainGenerator - use default generator with map latitudes
################################################################################
### Use this class with 'Planetfall'
### Only getLatitudeAtPlot() is changed to incorporate evalLatitude(), which
### gives the latitudes 0..90 for the actual map.
################################################################################
# lat = getLatitudeAtPlot( iX, iY )
# terrainVal = generateTerrainAtPlot( iX, iY )
################################################################################
class MST_TerrainGenerator(CvMapGeneratorUtil.TerrainGenerator):

	# mostly from 'Mars Now!' - SandSeaTerrainGenerator
	def generateTerrainAtPlot(self, iX, iY):

		# if not Mars, then use normal terrain generator
		if not bMars:
			return CvMapGeneratorUtil.TerrainGenerator().generateTerrainAtPlot( iX, iY )

		gc = CyGlobalContext()
		lat = self.getLatitudeAtPlot(iX,iY)
		pPlot = self.map.plot(iX, iY)

		if pPlot.isWater():
			pPlot.setPlotType(PlotTypes.PLOT_LAND, false, false)
			pPlot.setTerrainType(gc.getInfoTypeForString("TERRAIN_DESERT"), false, false)
			terrainVal = gc.getInfoTypeForString("TERRAIN_DESERT")

		else:
			terrainVal = self.terrainGrass
			if lat >= self.fTundraLatitude:
				terrainVal = choose( 66, self.terrainTundra, self.terrainTaiga )
			elif lat >= self.fTaigaLatitude:
				terrainVal = choose( 75, self.terrainTaiga, self.terrainGrass )
			elif lat < self.fGrassLatitude:
				terrainVal = choose( 90, self.terrainGrass, self.terrainPlains )
			else:
				desertVal = self.deserts.getHeight(iX, iY)
				plainsVal = self.plains.getHeight(iX, iY)
				if ((desertVal >= self.iDesertBottom) and (desertVal <= self.iDesertTop) and (lat >= self.fDesertBottomLatitude) and (lat < self.fDesertTopLatitude)):
					terrainVal = choose( 66, self.terrainDesert, self.terrainPlains )
				elif ((plainsVal >= self.iPlainsBottom) and (plainsVal <= self.iPlainsTop)):
					terrainVal = choose( 75, self.terrainPlains, self.terrainGrass )

		if (terrainVal == TerrainTypes.NO_TERRAIN):
			terrainVal = choose( 90, self.terrainPlains, self.terrainDesert )

		return terrainVal

	def getLatitudeAtPlot(self, iX, iY):
		"returns a value in the range of 0.0 (tropical) to 1.0 (polar)"
		lat = evalLatitude( map.plot(iX,iY), False )

		# Adjust latitude using self.variation fractal, to mix things up:
		lat += (128 - self.variation.getHeight(iX, iY))/(255.0 * 5.0)

		# Limit to the range [0, 1]:
		if lat < 0: lat = 0.0
		if lat > 1:	lat = 1.0
		return lat

################################################################################
########## CLASS MST_TerrainGenerator END
################################################################################


################################################################################
########## CLASS MST_FeatureGenerator - use default generator with map latitudes
################################################################################
### Use this class with 'Planetfall'
### Only getLatitudeAtPlot() is changed to incorporate evalLatitude(), which
### gives the latitudes 0..90 for the actual map.
################################################################################
# lat = getLatitudeAtPlot( iX, iY )
################################################################################
class MST_FeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
	def getLatitudeAtPlot(self, iX, iY):
		"returns a value in the range of 0.0 (tropical) to 1.0 (polar)"
		return evalLatitude( map.plot(iX,iY), False )

################################################################################
########## CLASS MST_FeatureGenerator END
################################################################################


################################################################################
######## INITIALIZE MapScriptTools - This is always executed
################################################################################
print "[MST] ########### pre-init MapScriptTools ########### Start"
getModInfo()
print "[MST] ########### pre-init MapScriptTools ########### End"
################################################################################


# Note: The following is more like a brain storm list, than a statement of intention
#
# todo (or not):
# ==============

# -------------- now
# MapScriptTools-API Manual - complete it, update it - this task will probably stay
# -------------- soon
# alternative to 'Lost Isle'
#  - 'Eden Valley' (two rows of mountains/hills, river in-between, several resources, ?? in the arctic ??)
# alternatives to 'Elemental Quarter':
#  - 'Devils Pentagram' (Death,Entropy,Shadow,Chaos,Meta -mana in pentagram form )
#  - 'Divine Circle' (Nature,Spirit,Life,Enchantment,Mind,Sun -mana in a circle)
# -------------- really soon now
# mapPrint.buildImprovementMap()
# (FinalFrontier) fully incorporate 'Final Frontier' maps
# (FFH) map option: crystallized mana / wildmana with(out) guardians - probably without!
# (FFH) featurePlacer - check if FlavourMod option is available and set
# include 'PlateTectonics' from 'FracturedWorld'
# include 'mapOptions' from 'FracturedWorld'
# -------------- soon enough
# prettify areas; specified either with areaID or (minXY,maxXY) - now global only
# percentify features: there are lots of forest types out there - include variety forests
# recognize more / newer mods; ?? how can i safely check for WoC ??
# include 'OccStart' from 'FracturedWorld'
# assignStartingPlots() / findStartingPlots for One-City-Challenge
#    humans start only on coastal lands near biggest ocean or all on one continent
# adjust for team-options in 'OccStart'
# -------------- sooner or later
# balance on wider scale and two tiers: (aluminum,uranium,mithril,(reagens?),oil,(coal?)) within 7-radius
#    and other, earlier resources (copper,iron,horses,mana) within 5-radius?
#    may have to adjust for players / map-plots ratio ?
# better missing boni recognition? (check all terrain/features against 3 is..() -> build list, check list)
#    no sense to try and place bananas without having a jungle
# balance farming - is that really needed? I think i always get an animal/grain already
# optional popup with info & map-stats
# more individual names for landmarks
# build river-lists of existing rivers
# mst.riverMaker.addRegionRivers() - build rivers from riverList
# (Planetfall) starting-plots: use default only when 'scattered landing pods' option is true
# remove more debugging code
# -------------- later
# mapRegions: add template as parameter, organize (some) template elements
# mapRegions: build in four stages: preRivers, Rivers, postRivers, postNormalize
# mapRegions: better register and check mechanism, priorities if map is to small for all
# put mapRegions together in MapRegionTools.py ??
# (Planetfall) trenches and shelves - changes sometimes, not pretty, seems not quite right - make own concept?
# mst.CivFolders() - write maps to different file, append to each other (if desired?, if same mod?, if same map?)
# Planetfall special region?
# look closely at region generating with CvMapGeneratorUtil.MultilayeredFractal.generatePlotsInRegion()
# -------------- much later
# produce events for my landmarks ... would have to be separate
# multiplayer compatibility? how? ... no idea what's involved here. See no reason why it shouldn't be already
# (Final Frontier) FFront-map special regions? Wormhole construction? probably not  ... but then again...
# starting-plot management?? definitly not  ... well...
# incorporate flavourmod in some form??? no way  ... hmm...
# -------------- much later, if ever
# other languages for landmarks???, for the log??? this would be big  ... someone else whould have to do that

# Known Errors
# ============
# Check for BBAI and DLL-Patch tests only one specific feature/tag. Apparently sometimes this check is not enough.
# "Thomas' War": missing features: FEATURE_DEAD_FOREST, FEATURE_EXOTIC_MIN_CORAL_TWO

# -------------------------------------------------------
# 'Don't call this a bug - it's an undocumented feature!'


'''
MapScriptTools Manual and API  Ver.: 1.00
=========================================

Introduction:
-------------
If you're a modder working (or playing!) with map-scripts, this is for you!

The tools in this file allow you to:
 1) Transform any map-script into one suitable for 'Planetfall' or 'Mars Now!'.
	1a) Use a template that for most mapscripts has to be only moderately adjusted.
 2) Introduce new terrains into any map-script.
	2a) Put Marsh Terrain on the map. If the mod supports it.
	2b) Put Deep Ocean Terrain on the map. If the mod supports it.
 3) Create odd regions on the map:
	3a) 'The Big Bog', a flat, marshy, somewhat round region, probably with a lake and some rivers within it.
	3b) 'The Big Dent', a mountainous, somewhat oval region, probably with a volcano and several
		rivers flowing from it.
	3c) 'Elemental Quarter', the place where elemental mana nodes meet. Earth, Water, Air and Fire nodes
		influence the quarter of featureless terrain behind them. (For FFH only)
	3d) The lost 'Isle Of Atlantis' / 'Numenor Island', a small, isolated island with city-ruins, roads,
		and perhaps some intact improvements. If allowed by the mod, some other goodies may also appear.
 4) Put mod-dependent features on the map:
	4a) Kelp on coastal plots
	4b) Haunted Lands in deep forest, deep desert, within and around marshes, near ruins and mountain passes.
	4c) Crystal Plains on snowy flatland plots.
 5) Greatly expand upon the BonusBalancer class from Warlords in CyMapGeneratorUtil.py.
	Allows for mod-specific bonus-lists (currenty only Civ and FFH, but you can supply your own).
	5a) Gives each player a fair chance to find the neccessary resources within a reasonable radius.
		If that radius overlaps with your neighbors, you may have to fight over that resource anyway.
	5b) Places missing boni (those boni which should have been but for some reason weren't placed by addBonus()).
	5c) Moves some minerals [Copper,Iron,Mithril,Uranium,Silver] placed on flatlands to nearby hills.
		Create those hills if necessary and wanted.
 6) Place rivers on the map.
	6a) Enable building rivers starting at the sea and moving upriver.
	6b) Put a river (or two) on smaller islands.
	6c) Automatically start river(s) from lake(s).
	6d) Produce river-lists. Print their coordinates. (As yet only of those rivers created by buildRiver())
 7) Allow teams to have nearby, separated or random starting-plots.
 8) Print maps to the Python log at "...\My Documents\My Games\Beyond the Sword\Logs\PythonDbg.log":
	8a) Area-Maps
	8b) Plot-Maps
	8c) Terrain-Maps (Normal and Planetfall) - allow user supplied list of terrain.
	8d) Feature-Maps (Normal and Planetfall) - allow user supplied list of features.
	8e) Bonus-Maps (Normal and Planetfall) - allow user supplied list of boni.
x   8f) Improvement-Maps (Normal and Planetfall) - allow user supplied list of improvements.
	8g) River-Maps (plots,river-flows and starting-plots)
	8h) Difference-Maps of an earlier map and the actual map can be produced to
		document the different stages of map building.
 9) Print stats of map and mod to the Python log at "...\My Documents\My Games\Beyond the Sword\Logs\PythonDbg.log".
10) Prettify maps:
   10a) Connect small lakes.
   10b) Connect small islands.
   10c) Connect small terrain patches.
   10d) Remove ice from edge of map.
   10e) Adjust plot / terrain frequency to given percentage.
   10f) Reduce peaks and volcanos for graphical beautification.
11) Find the path for Civ4, Mod or Log files
12) Groups of single funtion helpers:
   11a) Deal with areas.
   11b) Deal with (cardinal) directions.
   11c) Choose randomly - don't deal with dices anymore.
   11d) Convert between plot, index and coordinates.
   11e) Check numbers of neighbor plot-types, terrains, features.
x  11f) Validate and assign starting-plots
   11z) A whole lot of other goodies.
-----
x  Not implemented yet.


Installation:
-------------
Put the file MapScriptTools.py into the ...\Beyond the Sword\Assets\Python folder. (NOT CustomAssets!)
If you don't mind to see it as an option in the map selection of 'Custom Game', you can put it
into the ...\Beyond the Sword\PublicMaps folder, but that's the second best solution, as it won't work
if the mod disallows public maps in its ini-file (it may have other quirks - this isn't well tested).
'Planetfall' uses the PrivateMaps folder, here you whould either have to put it into the Python
folder, or change the ini-file to allow 'Planetfall' to use the PublicMaps folder.


Compatibility:
--------------
The 'MapScriptTools' are compatible with BtS 3.19.
I've run a short test with Warlords 2.13 and that worked fine too.
The above statements seem to imply compatibility to BtS 3.13 / 3.17, but this isn't tested.


Import MapScriptTools:
----------------------
Before using the MapScriptTools (MST), they have to be imported by the script.
Use 'import MapScriptTools as mst' somewhere at the beginning of your file.


Output:
-------
All reports go to the Python log normally at "...\My Documents\My Games\Beyond the Sword\Logs\PythonDbg.log".
You may have to enable logging by making sure the following option is set to 1 in
"...\My Documents\My Games\Beyond the Sword\civilization.ini":

; Enable the logging system
LoggingEnabled = 1


Initialization:
---------------
To use most of the goodies within the MapScriptTools, they have to be initialized.
The getModInfo() function is used for this purpose. It should be the first
MST function executed. Putting 'mst.getModInfo()' first into
beforeGeneration() seems like a good idea. Actually the function has optional
parameters which you probably want to use.


Functions:
----------

getModInfo( mapVersion=None, defLatitude=None, sMapInfo=None )
..............................................................
  Function: Initialize MapScriptTools and print basic map parameters to the log. Identify mod if possible.

  Parameter: mapVersion    string or None   Version of map-script
											default: None - version will not be printed.
			 defLatitude   string or None   String to be evaluated by evalLatitude(). The string-function can
											  only see x and y as variables and should return the latitude of
											  a plot at coordinates x,y as a value between 0 .. 90.
											default: None - noPolesGetLatitude(x,y) will be used as default
			 sMapInfo      string or None   String to be printed into the log with infos about the
											  selected map parameters.
											default: None - no info will be printed
  Return: -

evalLatitude( plot, bDegrees=True )
...................................
  Function: Evaluate defLatitude given in getModInfo(), to give the latitude for any plot.
			( MapScriptTools doesn't know how latitudes are calculated in each different map-script.
			  This is the mechanism to enable the internal functions to get the latitude for their
			  climate calculations. )

  Parameter: plot       plot   Plot on the map for which the latitude is sought.
			 bDegrees   bool   If True the result will be an integer between 0 .. 90,
							   else the result will be floating-point beween 0.0 .. 1.0, equator is zero.
  Return: Latitude of plot in the form indicated by bDegrees.


Instantiated Classes:
---------------------

class CivFolders:
instance: civFolders
.............................
Find out where the files are.
.............................
getModPaths()             Example:
--- vars ---              --------
civFolders.appName        Beyond the Sword
civFolders.userDir        ....\My Documents\My Games
civFolders.rootDir        ....\My Documents\My Games\Beyond the Sword
civFolders.logDir         ....\My Documents\My Games\Beyond the Sword\Logs
civFolders.appDir         ..\Civilization 4\Beyond the Sword
civFolders.modName        MyMod
civFolders.modFolder      Mods\MyMod
civFolders.modDir         ..\Civilization 4\Beyond the Sword\Mods\MyMod


class DeepOcean:
instance: deepOcean
.......................................................
put 'Deep Ocean' terrain into the middle of the oceans.
.......................................................
buildDeepOcean( dist=3, chDeep=80 )


class PlanetFallMap:
instance: planetFallMap
........................................................
All that's needed to change maps into 'Planetfall' maps.
........................................................
buildPfallOcean()
pFallTerrain = mapPfallTerrain( eTerrain, terList, plot, terrainGen=None )
buildPfallHighlands( iBaseChance=None )


class MapPrettifier:
instance: mapPrettifier
......................................
Something to make maps look beautiful.
......................................
connectifyLakes( chConnect=75 )
deIcifyEdges( iLat=66 )
hillifyCoast( chHills=66 )
beautifyVolcanos( chHills=66 )
lumpifyTerrain( targetTerrain, sourceTer1, sourceTer2=None )
bulkifyIslands( chConnect=66, maxIsle=4 )
percentifyTerrain( targetTerTuple, *sourceTerTuples )
percentifyPlots( targetPlotType, fTargetPlotPercent, data=None, terGenerator=None )


class MarshMaker:
instance: marshMaker
.....................................................
If the mod allows marsh-terrain, it can be made here.
.....................................................
bModHasMarsh = initialize( iGrassChance=5, iTaigaChance=10, tMarshHotRange=(0,18), tMarshColdRange=(45,63) )
convertTerrain( tAreaRange=None, areaID=None )
iArid = getAridity()
normalizeMarshes()


class MapRegions:
instance: mapRegions
.................................................................
Some regions on the map can be distinctive (and may have a name).
.................................................................
initialize( regDist=15 )
buildLostIsle( chance=33, minDist=7, bAliens=False )
centerPlot = theLostIsle( pCenterPlot, pList, bAliens )
buildBigBogs( iBogs=None )
namePlot = theBigBog( pCenterPlot, bBigBog=True, bBogLake=True )
buildBigDents( iDents=None )
namePlot = theBigDent( pCenterPlot, bSideways=None, chAccess=66 )
buildElementalQuarter( chEQ=66 )
namePlot = theElementalQuarter( pCenterPlot, temp )
addRegionExtras()


class FeaturePlacer:
instance: featurePlacer
..................................................
Put some common mod-dependent features on the map.
..................................................
placeKelp( chKelp=20, bAll=False, bLakes=False )
placeHauntedLands( chHaunted=6 )
placeCrystalPlains( chCrystal=25 )


class BonusBalancer:
instance: bonusBalancer
.........................................................................................
Deal with resources. Balance them and make sure all are on the map and where they belong.
.........................................................................................
initialize( bBalanceOnOff=True, bMissingOnOff=True, bMineralsOnOff=True, bWideRange=False )
normalizeAddExtras( *lResources )
bSkip = isSkipBonus( iBonusType )
bValid = isBonusValid( eBonus, pPlot, bIgnoreUniqueRange, bIgnoreOneArea, bIgnoreAdjacent )
addMissingBoni()
moveMinerals( lMineralsToMove=None )


class RiverMaker:
instance: riverMaker
.............................................................................................
Build rivers coming either down from the mountains or up from the sea. Put rivers on islands.
.............................................................................................
buildRiver( pStartPlot, bDownFlow=True, ecNext=None, ecOri=None, iThisRiverID=None, riverList=None )
islandRivers( minIsle=6, maxIsle=50, areaID=None )
buildRiversFromLake( lakeAreaID=None, chRiver=66, nRivers=1, minLake=1 )
sList = outRiverList( riverList )
bEdge = isEdgeDirection( self, plot, ecDir )
bRiver =  hasRiverAtPlot( plot )
bCorner = hasRiverAtSECorner( plot )
bCorner = hasCoastAtSECorner( plot )
bCorner = hasPlotTypeAtSECorner( plot, plotType )
eCard = getBestFlowDir( plot, bDownFlow=True, bShort=False, eForbiddenList=[] )


class TeamStart:
instance: teamStart
.........................................................
Put starting-plots of team members together or separated.
.........................................................
placeTeamsTogether( bTogether=False, bSeparated=False )
bTeams = getTeams()


class MapPrint:
instance: mapPrint
.................................
Have a look at what you've built.
.................................
initialize()
definePrintMap( lines, charsPerPlot, linesPerPlot, mapTitle="", region=None, offset=None, mapLegend="" )
printMap( diffDict=None )
bSuccess = buildDiffMap( newDict, oldDict )
buildAreaMap( bDiffDict=False, sTitle=None, region=None, areaID=None, areaDict=None )
buildPlotMap( bDiffDict=False, sTitle=None, region=None, data=None )
buildTerrainMap( bDiffDict=False, sTitle=None, region=None, terrainDict=None, showPlots=True )
buildFeatureMap( bDiffDict=False, sTitle=None, region=None, featureDict=None, showPlots=True )
buildBonusMap( bDiffDict=False, sTitle=None, region=None, bonusDict=None, showPlots=True )
buildRiverMap( bDiffDict=False, sTitle=None, region=None )


class MapStats:
instance: mapStats
...............................
Don't you just love statistics?
...............................
mapStatistics( bFullVersion=True )
tPlotStats = statPlotCount( txt=None )
showContinents( txt=None, minPlots=3, bWater=False )
sTechs = getTechList( prefix = "", bTechLevels=True )
listPlayers = getCivPlayerList()
sprint = sprintActiveCivs( showTeams=False, showTraits=False, showHumans=False )


class RandomList:
instance: randomList
.......................................
Just little helpers to randomize lists.
.......................................
newlist = xshuffle( oriList )
shuffle( oriList )
countList = randomList.randomCountList( count )


Uninstantiated Classes:
-----------------------

class MST_TerrainGenerator(CvMapGeneratorUtil.TerrainGenerator):
...............................................................
Make sure the right latitudes are used when generating terrain,
also produces terrain for 'Mars Now!'.
...............................................................
terrainVal = generateTerrainAtPlot( iX, iY ):
lat = getLatitudeAtPlot( iX, iY )


class MST_FeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
................................................................
Make sure the right latitudes are used when generating features.
................................................................
lat = getLatitudeAtPlot( iX, iY )


Useful Functions:
-----------------
There are quite a few little 'helper' files near the top of this file,
which may well be usefull to you. If you used 'import MapScriptTools as mst',
you can use them all by putting 'mst.' before the call.
Have a look and feel free to do with them what you want.


Useful Constants:
-----------------
mst.bPfall   True,False
			 indicates if this mod is 'Planetfall' or a modmod
			 ( checks for BONUS_FUNGICIDE )

mst.bMars    True,False
			 indicates if this mod is 'Mars Now!' or a modmod
			 ( checks for 'Mars, Now!' in pedia )

mst.bFFH     True,False
			 indicates if this mod is 'Fall From Heaven 2' or a modmod
			 ( checks for BONUS_MANA )

mst.bFFront  True,False
			 indicates if this mod is 'Final Frontier' or a modmod
			 ( checks for FEATURE_SOLAR_SYSTEM )

mst.bPatch   True,False
			 indicates if the 'CvGameCoreDLL.dll' of this mod incorporates the 'Unofficial Patch'
			 ( checks results of plot.getLatitude() )

mst.bBUG     True,False
			 indicates if this mod is or incorporates the BUG-Mod

mst.bBBAI    True,False
			 indicates if this mod is or incorporates the BBAI-Mod

mst.bAIAuto  True,False
			 indicates if this mod incorporates 'AI AutoPlay'


Notes:
------
These tools are for the english version only.
Several tests depend on text found in various xml-files. To be more precise:
The english text! Of the checks mentioned that would be bBUG, bBBAI and bAIAuto
together with most other mod-recognition checks.
Any failure of the tests will probably just affect the stats though.

Python 2.4 doesn't really have much of a concept for private data. The
class methods below the ---private--- line are as readily accessible as
the others, but they are not part of the API and thus subject to change
without notice.
( Just like anything else really - I'm giving no guarantees, but I might think twice.)


Included Mapscripts:
--------------------
To use the MapScriptTools with existing mapscripts, just put the included template-script
into them and modify as needed. To demonstarte how it is done I've included several altered
mapscripts. Some mapscripts required additional changes - sorry, but it's not quite automated (yet)
and you still need some understanding of what you are doing.

All maps can be used with 'Planetfall' or 'Mars Now!'.
All maps can (and will) produce Marsh terrain, if the mod supports it.
All maps can (and will) produce Deep Ocean terrain, if the mod supports it.
All maps allow for at least two more map sizes beyond 'Huge', if the mod supports them
All maps may add Map Regions ( BigDent, BigBog (not Mars), ElementalQuarter (FFH only), LostIsle ).
All maps may add Map Features ( Kelp, HauntedLands, CrystalPlains ), if supported by mod (FFH only).
All maps add some rivers on small islands and from lakes
All maps support Team Start options.
All maps support any number of players, depending on the mod.
All maps produce printed maps in "...\My Documents\My Games\Beyond the Sword\Logs\PythonDbg.log"
All maps produce printed statistics in "...\My Documents\My Games\Beyond the Sword\Logs\PythonDbg.log"
If 'Planetfall' is the active mod, usually the planetfall-default starting plot finder will be used.
If 'Mars Now!' is the active mod, the Team Start option will be suppressed.
If 'Mars Now!' is the active mod, oceans and lakes are converted to desert.
Most maps use balanced resources, add missing boni and try to move some minerals to nearby hills.

Earth3_162_mst.py             by jkp1187 --> http://forums.civfanatics.com/showthread.php?t=253927
   - Adjusted starting-plot creation using: 'Temudjins Cool Starting Plots'
   - Added New Zealand, Madagascar and changed Japan a bit.
   - Added Himalayas (single BigDent at special place)

Erebus_107b_mst.py            by Cephalo --> http://forums.civfanatics.com/showthread.php?t=261688
   - Uses default river-system. Wasn't able to insert the new rivers of mapRegions.
   - Opera already introduced placing of Kelp, HauntedLands, CrystalPlains for FFH

Medium_and_Small_110_mst.py   by Sirian (Civ4 original)

PerfectWorld_206_mst.py       by Cephalo --> http://forums.civfanatics.com/showthread.php?t=310891
   - I had to fiddle a bit in generateTerrainTypes() to transform the generated terrainList
   - Uses default river-system. Wasn't able to insert the new rivers of mapRegions.

Sea_Highlands_120_mst.py      by Sirian (Civ4 original)
   - vbraun already added an option and changed some values; I changed some more to make ships useful.
   - The MapScriptTools template is at the bottom of the file.
   - Shows how to construct a moderatly complex evaluation string for evalLatitude().
   - Eliminate Whale and Pearls boni.
   - Flat map only.

SmartMap_920_mst.py           by surt --> http://forums.civfanatics.com/showthread.php?t=154989
   - Full BtS compatibility.
   - Use both .Civ4WorldBuilderSave and .CivBeyondSwordWBSave files.
   - Adjusted starting-plot creation using: 'Temudjins Cool Starting Plots'
   - Some adjustment of Map Options.
   - Lots of small changes in nearly all functions.

Tectonics_316_mst.py          by Laurent Di Cesare --> http://forums.civfanatics.com/showthread.php?t=149278
   - Adjusted starting-plot creation using: 'Temudjins Cool Starting Plots'

Ringworld3_100_mst.py         by Temudjin --> http://forums.civfanatics.com/showthread.php?t=300961
   - My very own map-script, using lots of MapScriptTools features.

FracturedWorld_100_mst.py     by Temudjin -->
   - My very own map-script, using lots of MapScriptTools features.


****************************************************************************************************
**  Thanks:                                                                                       **
**  -------                                                                                       **
**  I've looked into a lot of map-scripts and mod-code and learned much from the authors. I also  **
**  stole ideas and sometimes even parts of code, which I found useful. I'm sorry to say that     **
**  I don't remember all of my sources - my apologies and thank you all for your efforts.         **
**  Specifically I'd like to thank:                                                               **
**                                                                                                **
**  Ruff_Hi                                                                                       **
**   - Your 'Ring World' induced me into a deeper investigation of maps.                          **
**                                                                                                **
**  The CivFanatics Community                                                                     **
**   - For making all those wonderful maps and mods and                                           **
**     for providing the opportunity to have a look at how it's done.                             **
**                                                                                                **
**  The Civ4 Design Team                                                                          **
**   - By opening your game-engine, you really opend the world(s).                                **
****************************************************************************************************


For Reference:
----------------------------------------------------------------
The Map Building Process according to Temudjin
	--> also see Bob Thomas in "CvMapScriptInterface.py"
	(in ..\Assets\Python\EntryPoints)
----------------------------------------------------------------
0)     - Get Map-Options
0.1)     getNumHiddenCustomMapOptions()
0.2)     getNumCustomMapOptions()
0.3)     getCustomMapOptionDefault()
0.4)     isAdvancedMap()
0.5)     getCustomMapOptionName()
0.6)     getNumCustomMapOptionValues()
0.7)     isRandomCustomMapOption()
0.8)     getCustomMapOptionDescAt()
0.9)     - Get Map-Types
0.9.1)     isClimateMap()
0.9.2)     isSeaLevelMap()
1)     beforeInit()
2)     - Initialize Map
2.2)     getGridSize()
2.3.1)   getTopLatitude()					# always use both
2.3.2)   getBottomLatitude()				# always use both
2.4.1)   getWrapX()							# always use both
2.4.2)   getWrapY()							# always use both
3)     beforeGeneration()
4)     - Generate Map
4.1)     generatePlotTypes()
4.2)     generateTerrainTypes()
4.3)     addRivers()
4.4)     addLakes()
4.5)     addFeatures()
4.6)     addBonuses()
4.6.1)     isBonusIgnoreLatitude()*
4.7)     addGoodies()
5)     afterGeneration()
6)     - Select Starting-Plots
6.1)     minStartingDistanceModifier()
6.2)     assignStartingPlots()
7)     - Normalize Starting-Plots
7.1)     normalizeStartingPlotLocations()
7.2)     normalizeAddRiver()
7.3)     normalizeRemovePeaks()
7.4)     normalizeAddLakes()
7.5)     normalizeRemoveBadFeatures()
7.6)     normalizeRemoveBadTerrain()
7.7)     normalizeAddFoodBonuses()
7.7.1)     isBonusIgnoreLatitude()*
7.8)     normalizeGoodTerrain()
7.9)     normalizeAddExtras()
7.9.1)     isBonusIgnoreLatitude()*
8 )    startHumansOnSameTile()

* used by default 'CyPythonMgr().allowDefaultImpl()' in:
  addBonuses(), normalizeAddFoodBonuses(), normalizeAddExtras()
------------------------------------------------------------------


An Example Template:
--------------------
Just put the following into your map-script, comment-out / delete what you don't want and
make a few necessary adjustments. You probably have to rename some of your functions too.
Feel free to delete any superfluous comments if they distract to much:

##################################################################################
## MapScriptTools Interface by Temudjin
##################################################################################
import MapScriptTools as mst

# The following two functions are not exactly neccessary, but they should be
# in all map-scripts. Just comment them out if they are already in the script.
# ----------------------------------------------------------------------------
def getVersion():
	return "1.20a"
def getDescription():
	return "MyMapScript - looks like a game world. Ver." + getVersion()

# this function will be called early by the system, before any parts of tha map are created
# - define your latitude formula, get the map-version
# - initialize the MapScriptTools
# - initialize MapScriptTools.BonusBalancer - decide which parts your script wants to use
# -----------------------------------------------------------------------------------------
def beforeGeneration():
	print "-- beforeGeneration()"

	# Create evaluation string for getLatitude(x,y); note that functions of the mapscript
	# will not be visible at evaluation-time, only x and y can be seen.
	# The result should be between 0 .. 90, but a negative value will be converted.
	# i.e.: compGetLat = "((y/%5.1f) - %3.1f) * 90" % ( CyMap().getGridHeight()-1, 1 )
	#     - which would give you half a world from equator to south pole.
	# Omitting compGetLat or setting it to None, will result in using the default function,
	# which will give equally distributed latitudes between both poles.

	# Initialize MapScriptTools
	compGetLat = None
	# Create mapInfo string
	mapInfo = ""
	for opt in range( getNumCustomMapOptions() ):
		nam = getCustomMapOptionName( [opt] )
		sel = CyMap().getCustomMapOption( opt )
		txt = getCustomMapOptionDescAt( [opt,sel] )
		mapInfo += "%27s:   %s\n" % ( nam, txt )
	mst.getModInfo( getVersion(), compGetLat, mapInfo )

	# Initialize MapScriptTools.BonusBalancer
	# balance boni: False, place missing boni: True, move minerals: True
	mst.bonusBalancer.initialize( False, True, True )

	# Some scripts actually have an option for balancing resources.
	# in this case the call would be somewhat like this:
	# mst.bonusBalancer.initialize( (CyMap().getCustomMapOption(2)==1), True, True )

	# If the mapscript already has a function beforeGeneration(), then
	# rename it to beforeGeneration2() and uncomment the next line
#	beforeGeneration2()

# This function will be called by the system, after generatePlotTypes() and before addRivers()
# - print the plot-map and hold result to check differences to the next call
# - build highlands for 'Planetfall'
# - prettify plots
# - handle 'Planetfall' mod terrain
# If the map-script does more than just call the generator in generateTerrainTypes(), you will
# have to take a closer look.
# --------------------------------------------------------------------------------------------
def generateTerrainTypes():
	print "-- generateTerrainTypes()"

	# print a plotMap; allow for differenceMap with next call
	mst.mapPrint.buildPlotMap( True, "generateTerrainTypes()" )

	# 'Planetfall' uses ridges and highlands. To utilize them fully, you will
	# probably want to have a hilly terrain - if you already use
	# a highland mapscript, you may want to comment-out the following line.
	mst.planetFallMap.buildPfallHighlands()

	# Prettify the map - change coastal peaks to hills with 80% chance; default: 66%
	mst.mapPrettifier.hillifyCoast( 80 )

	# If your active mod is 'Planetfall', you will have to use a different terrainGenerator.
	if mst.bPfall or mst.bMars:

		# 'Planetfall' uses shelves and trenches to spread and stop the fungus.
		# The oceans have to be a bit reorganized to accommodate the different realities.
		mst.planetFallMap.buildPfallOcean()

		# 'Planetfall' or 'Mars Now!' need to use this TerrainGenerator to use the map-latitudes.
		terraingen = mst.MST_TerrainGenerator()

	else:
		# Scripts may already have their own TerrainGenerator.
		# terraingen = ThisMapTerrainGenerator()
		# If the script doesn't have it's own, you use this one too (same as 'Planetfall').
		terraingen = mst.MST_TerrainGenerator()

	# Create the terrain and return the result.
	terrainTypes = terraingen.generateTerrain()
	return terrainTypes

# this function will be called by the system, after generateTerrainTypes() and before addLakes()
# - Generate marsh terrain - converts some grass and tundra to marsh within two latitude zones.
# - build some odd regions ('The Big Bog', 'The Big Dent', 'Elemental Quarter')
# - prettify terrain
# - make rivers on smaller islands
# ----------------------------------------------------------------------------------------------
def addRivers():
	print "-- addRivers()"

	# Generate DeepOcean-terrain if mod allows for it
	mst.deepOcean.buildDeepOcean()

	# Generate marsh-terrain within latitude zones (default: 5, 10, (0,18), (45,63) ).
	# The frequency of transformation as well as the zones may be changed by first
	# calling mst.marshMaker.initialize() with the appropriate parameters.
	mst.marshMaker.initialize( 4, 20, (0,25), (50,75) )
	mst.marshMaker.convertTerrain()
	# Solidify marsh between 2 [Arid,LowSea] and 8 [Tropical,HighSea] percent.
	if not mst.bPfall:
		if mst.bMarsh:
			marshPer = 5 - mst.marshMaker.getAridity()
			mst.mapPrettifier.percentifyTerrain( (mst.etMarsh,marshPer), (mst.etTaiga,1), (mst.etGrass,2) )

	# Build between 0..3 mountain-ranges.
	mst.mapRegions.buildBigDents()

	# Build between 0..3 bog-regions.
	mst.mapRegions.buildBigBogs()

	# build ElementalQuarter (66% chance). - ignored if not FFH
	mst.mapRegions.buildElementalQuarter()

	# Some scripts produce more chaotic terrain than others. You can create more connected
	# (bigger) deserts by converting surrounded plains and grass.
	# Prettify the map - create better connected deserts and plains
	mst.mapPrettifier.lumpifyTerrain( mst.etDesert, mst.etPlains, mst.etGrass )
	mst.mapPrettifier.lumpifyTerrain( mst.etPlains, mst.etDesert, mst.etGrass )
	# Sprout rivers from lakes.
	mst.riverMaker.buildRiversFromLake()		# 66% chance to get one river from each lake

	# If the script already has an addRivers() function, you want to rename it and call it here.
#	addRivers2()									   # call renamed script function
	# If the script did not have an addRivers() function, this was called instead.
	CyPythonMgr().allowDefaultImpl()				# don't forget this

	# Put rivers on small islands.
	mst.riverMaker.islandRivers()					# islands between 6 and 50 tiles

# This function will be called by the system, after addRivers() and before addFeatures()
# - don't add lakes on Mars
# ------------------------------------------------------------------------------------
def addLakes():
	print "-- addLakes()"
	if not mst.bMars:
		CyPythonMgr().allowDefaultImpl()

# This function will be called by the system, after addLakes() and before addBonuses()
# - prettify lakes
# - handle 'Planetfall' mod features
# - prettify volcanos
# If the map-script does more than just call the generator in addFeatures(), you will
# have to take a closer look.
# ------------------------------------------------------------------------------------
def addFeatures():
	print "-- addFeatures()"

	# Prettify the map - kill off spurious lakes; default: 75% chance
	mst.mapPrettifier.connectifyLakes( 90 )

	# If your active mod is 'Planetfall', you have to call a different generator.
	if mst.bPfall or mst.bMars:
		# 'Planetfall' or 'Mars Now!' need to use this FeatureGenerator to use the map-latitudes.
		featuregen = mst.MST_FeatureGenerator()
		featuregen.addFeatures()
	else:
		# Rename the scripts addFeatures() function and call it here.
		addFeatures2()							# call renamed script function
		# If the script doesn't have it's own generator, you use this one too:
#		terraingen = mst.MST_FeatureGenerator()
#		featuregen.addFeatures()

	# Prettify the map - transform coastal volcanos; default: 66% chance
	mst.mapPrettifier.beautifyVolcanos( 80 )

# This function will be called by the system, after the map was generated, after the
# starting-plots have been choosen, at the start of the normalizing process.
# You will only need this function, if you want to use the teamStart options.
# In this example we assume that the script has a custom-option for team starts with
# 4 options: 'nearby', 'separated', 'randomize', 'ignore'.
# ----------------------------------------------------------------------------------
def normalizeStartingPlotLocations():
	print "-- normalizeStartingPlotLocations()"

	# Build Lost Isle
	# - this region needs to be placed after starting-plots are first assigned
	# - 33% chance to build lost isle, with minimum distance of 7 to next continent. 33% of those
	#   islands where build by aliens and may have intact remnants of an advanced roadway system.
	mst.mapRegions.buildLostIsle( chance=33, minDist=7, bAliens=mst.choose(33,True,False) )

	# Handle Team Start Option
	if CyMap().getCustomMapOption(2) == 0:
		CyPythonMgr().allowDefaultImpl()							# by default civ places teams near to each other
		# mst.teamStart.placeTeamsTogether( True, True )	# use teamStart to place teams near to each other
	elif CyMap().getCustomMapOption(2) == 1:
		mst.teamStart.placeTeamsTogether( False, True )		# shuffle starting-plots to separate teams
	elif CyMap().getCustomMapOption(2) == 2:
		mst.teamStart.placeTeamsTogether( True, True )		# randomize starting-plots (may be near or not)
	else:
		mst.teamStart.placeTeamsTogether( False, False )	# leave starting-plots alone

# prevent additional rivers on Mars
def normalizeAddRiver():
	print "-- normalizeAddRiver()"
	if not mst.bMars:
		CyPythonMgr().allowDefaultImpl()

# prevent additional lakes on Mars
def normalizeAddLakes():
	print "-- normalizeAddLakes()"
	if not mst.bMars:
		CyPythonMgr().allowDefaultImpl()

# prevent terrain changes on Mars
def normalizeRemoveBadTerrain():
	print "-- normalizeRemoveBadTerrain()"
	if not mst.bMars:
		CyPythonMgr().allowDefaultImpl()

# prevent terrain changes on Mars
def normalizeAddGoodTerrain():
	print "-- normalizeAddGoodTerrain()"
	if not mst.bMars:
		CyPythonMgr().allowDefaultImpl()

# This function will be called by the system, after the map was generated, after the
# starting-plots have been choosen, at the end of the normalizing process and
# before startHumansOnSameTile() which is the last map-function so called.
# - balance boni (depending on initialization also place missing boni and move minerals)
# - give names and boni to special regions
# - print plot-map and the difference-map to the call before
# - print other maps
# - print river-map with plots, rivers and starting-plots
# - print map and mod statistics
# --------------------------------------------------------------------------------------
def normalizeAddExtras():
	print "-- normalizeAddExtras()"

	# Balance boni, place missing boni and move minerals depending on initialization.
	mst.bonusBalancer.normalizeAddExtras()

	# If the script already has a normalizeAddExtras() function, you want to rename it and call it here.
	# normalizeAddExtras2()                 # call renamed script function
	# If the script already uses a bonusBalancer, you need to comment it out in
	# the original normalizeAddExtras(). You also want to look into addBonusType()
	# and comment the balancer out there too.
	# In fact if there isn't done anything else in those functions besides balancing,
	# you should comment-out both functions.
	CyPythonMgr().allowDefaultImpl()        # do the default housekeeping

	# Give extras (names and boni) to special regions
	# FFH does a lot housekeeping, but some special regions may want to overrule that.
	mst.mapRegions.addRegionExtras()

	# Place special features on map
	mst.featurePlacer.placeKelp()
	mst.featurePlacer.placeHauntedLands()
	mst.featurePlacer.placeCrystalPlains()

	# Kill ice-feature on warm edges.
	# Regardless of latitude, if Y-axis isn't wrapped Civ4 puts ice on the north- and southpoles.
	mst.mapPrettifier.deIcifyEdges()

	# Print plotMap and differencePlotMap
	mst.mapPrint.buildPlotMap( True, "normalizeAddExtras()" )

	# Print areaMap
	mst.mapPrint.buildAreaMap( False, "normalizeAddExtras()" )

	# Print terrainMap and differenceTerrainMap
	mst.mapPrint.buildTerrainMap( True, "normalizeAddExtras()" )

	# Print featureMap
	mst.mapPrint.buildFeatureMap( False, "normalizeAddExtras()" )

	# Print bonusMap
	mst.mapPrint.buildBonusMap( False, "normalizeAddExtras()" )

	# Print riverMap
	mst.mapPrint.buildRiverMap( False, "normalizeAddExtras()" )

	# Print mod and map statistics
	mst.mapStats.mapStatistics()

# This function will be called at odd times by the system.
# 'Planetfall' wants nearer starting-plots
# If the script already has this function, return that result instead of zero or rename it.
def minStartingDistanceModifier():
	if mst.bPfall: return -25
	return 0
##################################################################################

'''





