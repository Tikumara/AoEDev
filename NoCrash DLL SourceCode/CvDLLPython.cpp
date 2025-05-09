#include "CvGameCoreDLL.h"
#include "CyMap.h"
#include "CyPlayer.h"
#include "CyPlot.h"
#include "CyGame.h"
#include "CyUnit.h"
#include "CyGlobalContext.h"
#include "CyCity.h"

void CyCityPythonInterface1(python::class_<CyCity>& x);
/*************************************************************************************************/
/**	Valk Tweak								07/23/10											**/
/**																								**/
/**						Required to allow Debug DLLs with the new makefile						**/
/*************************************************************************************************/
void CyCityPythonInterface2(python::class_<CyCity>& x);
/*************************************************************************************************/
/**	Tweak									END													**/
/*************************************************************************************************/
void CyPlotPythonInterface1(python::class_<CyPlot>& x);
void CyPlayerPythonInterface1(python::class_<CyPlayer>& x);
void CyPlayerPythonInterface2(python::class_<CyPlayer>& x);
void CyUnitPythonInterface1(python::class_<CyUnit>& x);
void CyGlobalContextPythonInterface1(python::class_<CyGlobalContext>& x);
void CyGlobalContextPythonInterface2(python::class_<CyGlobalContext>& x);
void CyGlobalContextPythonInterface3(python::class_<CyGlobalContext>& x);
void CyGlobalContextPythonInterface4(python::class_<CyGlobalContext>& x);
void CyGamePythonInterface();
void CyRandomPythonInterface();
void CyEnumsPythonInterface();
void CyTeamPythonInterface();
void CyAreaPythonInterface();
void CyStructsPythonInterface1();
/*************************************************************************************************/
/**	Jean Tweak								11/23/08											**/
/**																								**/
/**						Required for avoiding useless errors during debug						**/
/*************************************************************************************************/
/**								---- Start Original Code ----									**
void CyMapPythonInterface();
/**								----  End Original Code  ----									**/
void CyMapPythonInterface1(python::class_<CyMap>& x);
void CyMapPythonInterface2(python::class_<CyMap>& x);
/*************************************************************************************************/
/**	Tweak									END													**/
/*************************************************************************************************/
void CyMapGeneratorPythonInterface();
void CyInfoPythonInterface1();
void CyInfoPythonInterface2();
void CyInfoPythonInterface3();
void CyInfoPythonInterface4();
void CySelectionGroupInterface();
void CyArtFileMgrPythonInterface();
void CyGameTextMgrInterface();
void CyHallOfFameInterface();
void CyGameCoreUtilsPythonInterface();
void CyMessageControlInterface();
/*************************************************************************************************/
/**	Debugging							02/05/10								Snarko			**/
/**																								**/
/**				So that we may measure time taken in and between functions						**/
/*************************************************************************************************/
void CySnarkoProfilerPythonInterface();
/*************************************************************************************************/
/**	Debugging									END												**/
/*************************************************************************************************/

//
//
//
DllExport void DLLPublishToPython()
{
	CyEnumsPythonInterface();
	CyGamePythonInterface();
	CyRandomPythonInterface();
	CyTeamPythonInterface();
	CyAreaPythonInterface();
	CyStructsPythonInterface1();
/*************************************************************************************************/
/**	Jean Tweak								11/23/08											**/
/**																								**/
/**						Required for avoiding useless errors during debug						**/
/*************************************************************************************************/
/**								---- Start Original Code ----									**
	CyMapPythonInterface();
/**								----  End Original Code  ----									**/
/*************************************************************************************************/
/**	Tweak									END													**/
/*************************************************************************************************/
	CyMapGeneratorPythonInterface();
	CySelectionGroupInterface();
	CyArtFileMgrPythonInterface();
	CyGameTextMgrInterface();
	CyInfoPythonInterface1();
	CyInfoPythonInterface2();
	CyInfoPythonInterface3();
	CyInfoPythonInterface4();
	CyHallOfFameInterface();
	CyGameCoreUtilsPythonInterface();
	CyMessageControlInterface();

	//
	// large interfaces which can be split across files if need be
	//
/*************************************************************************************************/
/**	Jean Tweak								11/23/08											**/
/**																								**/
/**						Required for avoiding useless errors during debug						**/
/*************************************************************************************************/
	python::class_<CyMap> map ("CyMap");		// define map class
	CyMapPythonInterface1(map);					// publish it's methods
	CyMapPythonInterface2(map);					// publish it's methods
/*************************************************************************************************/
/**	Tweak									END													**/
/*************************************************************************************************/
	python::class_<CyCity> city ("CyCity");		// define city class
	CyCityPythonInterface1(city);				// publish it's methods
/*************************************************************************************************/
/**	Valk Tweak								07/23/10											**/
/**																								**/
/**						Required to allow Debug DLLs with the new makefile						**/
/*************************************************************************************************/
	CyCityPythonInterface2(city);
/*************************************************************************************************/
/**	Tweak									END													**/
/*************************************************************************************************/

	python::class_<CyPlayer> player ("CyPlayer");	// define player class
	CyPlayerPythonInterface1(player);				// publish it's methods
	CyPlayerPythonInterface2(player);				// publish it's methods

	python::class_<CyUnit> unit ("CyUnit");		// define unit class
	CyUnitPythonInterface1(unit);				// publish it's methods

	python::class_<CyPlot> plot ("CyPlot");		// define plot class
	CyPlotPythonInterface1(plot);				// publish it's methods

	python::class_<CyGlobalContext> gc ("CyGlobalContext");	// define globals class
	CyGlobalContextPythonInterface1(gc);					// publish it's methods
	CyGlobalContextPythonInterface2(gc);					// publish it's methods
	CyGlobalContextPythonInterface3(gc);					// publish it's methods
	CyGlobalContextPythonInterface4(gc);					// publish it's methods
/*************************************************************************************************/
/**	Debugging							02/05/10								Snarko			**/
/**																								**/
/**				So that we may measure time taken in and between functions						**/
/*************************************************************************************************/
	CySnarkoProfilerPythonInterface();
/*************************************************************************************************/
/**	Debugging									END												**/
/*************************************************************************************************/
}