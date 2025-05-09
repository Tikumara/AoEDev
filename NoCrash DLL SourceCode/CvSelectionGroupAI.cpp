// selectionGroupAI.cpp

#include "CvGameCoreDLL.h"
#include "CvSelectionGroupAI.h"
#include "CvPlayerAI.h"
#include "CvMap.h"
#include "CvPlot.h"
#include "CvTeamAI.h"
#include "CvDLLEntityIFaceBase.h"
#include "CvGameCoreUtils.h"
#include "FProfiler.h"
#include "CVInfos.h"

// Public Functions...

CvSelectionGroupAI::CvSelectionGroupAI()
{
	AI_reset();
}


CvSelectionGroupAI::~CvSelectionGroupAI()
{
	AI_uninit();
}


void CvSelectionGroupAI::AI_init()
{
	AI_reset();

	//--------------------------------
	// Init other game data
}


void CvSelectionGroupAI::AI_uninit()
{
}


void CvSelectionGroupAI::AI_reset()
{
	AI_uninit();

	m_iMissionAIX = INVALID_PLOT_COORD;
	m_iMissionAIY = INVALID_PLOT_COORD;

	m_bForceSeparate = false;

	m_eMissionAIType = NO_MISSIONAI;

	m_missionAIUnit.reset();

	m_bGroupAttack = false;
	m_iGroupAttackX = -1;
	m_iGroupAttackY = -1;
}


void CvSelectionGroupAI::AI_separate()
{
	CLLNode<IDInfo>* pEntityNode;
	CvUnit* pLoopUnit;

	pEntityNode = headUnitNode();

	while (pEntityNode != NULL)
	{
		pLoopUnit = ::getUnit(pEntityNode->m_data);
		pEntityNode = nextUnitNode(pEntityNode);

		pLoopUnit->joinGroup(NULL);
		if (pLoopUnit->plot()->getTeam() == getTeam())
		{
			pLoopUnit->getGroup()->pushMission(MISSION_SKIP);
		}
	}
}

/************************************************************************************************/
/* BETTER_BTS_AI_MOD                      06/02/09                                jdog5000      */
/*                                                                                              */
/* General AI, Bugfix                                                                           */
/************************************************************************************************/
void CvSelectionGroupAI::AI_separateNonAI(UnitAITypes eUnitAI)
{
	CLLNode<IDInfo>* pEntityNode;
	CvUnit* pLoopUnit;

	pEntityNode = headUnitNode();

	while (pEntityNode != NULL)
	{
		pLoopUnit = ::getUnit(pEntityNode->m_data);
		pEntityNode = nextUnitNode(pEntityNode);
		if (pLoopUnit->AI_getUnitAIType() != eUnitAI)
		{
			pLoopUnit->joinGroup(NULL);
			if (pLoopUnit->plot()->getTeam() == getTeam())
			{
				pLoopUnit->getGroup()->pushMission(MISSION_SKIP);
			}
		}
	}
}

void CvSelectionGroupAI::AI_separateAI(UnitAITypes eUnitAI)
{
	CLLNode<IDInfo>* pEntityNode;
	CvUnit* pLoopUnit;

	pEntityNode = headUnitNode();

	while (pEntityNode != NULL)
	{
		pLoopUnit = ::getUnit(pEntityNode->m_data);
		pEntityNode = nextUnitNode(pEntityNode);
		if (pLoopUnit->AI_getUnitAIType() == eUnitAI)
		{
			pLoopUnit->joinGroup(NULL);
			// Was potential crash in use of plot() if group emptied
			if (pLoopUnit->plot()->getTeam() == getTeam())
			{
				pLoopUnit->getGroup()->pushMission(MISSION_SKIP);
			}
		}
	}
}
void CvSelectionGroupAI::AI_separateImpassable()
{
	CLLNode<IDInfo>* pEntityNode;
	CvUnit* pLoopUnit;
	CvPlayerAI& kPlayer = GET_PLAYER(getOwner());

	pEntityNode = headUnitNode();

	while (pEntityNode != NULL)
	{
		pLoopUnit = ::getUnit(pEntityNode->m_data);
		pEntityNode = nextUnitNode(pEntityNode);
		if( (kPlayer.AI_unitImpassableCount(pLoopUnit->getUnitType()) > 0) )
		{
			pLoopUnit->joinGroup(NULL);
			if (pLoopUnit->plot()->getTeam() == getTeam())
			{
				pLoopUnit->getGroup()->pushMission(MISSION_SKIP);
			}
		}
	}
}

void CvSelectionGroupAI::AI_separateEmptyTransports()
{
	CLLNode<IDInfo>* pEntityNode;
	CvUnit* pLoopUnit;

	pEntityNode = headUnitNode();

	while (pEntityNode != NULL)
	{
		pLoopUnit = ::getUnit(pEntityNode->m_data);
		pEntityNode = nextUnitNode(pEntityNode);
		if ((pLoopUnit->AI_getUnitAIType() == UNITAI_ASSAULT_SEA) && (pLoopUnit->getCargo() == 0))
		{
			pLoopUnit->joinGroup(NULL);
			if (pLoopUnit->plot()->getTeam() == getTeam())
			{
				pLoopUnit->getGroup()->pushMission(MISSION_SKIP);
			}
		}
	}
}
/************************************************************************************************/
/* BETTER_BTS_AI_MOD                       END                                                  */
/************************************************************************************************/

/*************************************************************************************************/
/**	Improved spell usage				11/05/10				Moved/modified by Snarko		**/
/**								Potentially improves AI Spell Useage							**/
/**							Potentially improves AI Range Damage Useage							**/
/**					Moved from CvPlayerAI::AI_movementPriority to prevent CtD					**/
/*************************************************************************************************/
bool CvSelectionGroupAI::AI_PreUpdate()
{
	CvUnit* pLoopUnit;

	for (int iI = 0; iI < getNumUnits(); iI++)
	{
		pLoopUnit = getUnitAt(iI);
		if (!pLoopUnit->isDead()) //Another unit casting a spell could have killed this one
		{
/*************************************************************************************************/
/**	Tweak							05/05/11								Snarko				**/
/**			Making ranged attacks cost a movement point and adjusting the AI.					**/
/*************************************************************************************************/
/**								---- Start Original Code ----									**
			//We need ranged attacks before spells in case the spell kill the unit
			pLoopUnit->AI_rangeAttack(pLoopUnit->airRange());
/**								----  End Original Code  ----									**/
/*************************************************************************************************/
/**	Tweak									END													**/
/*************************************************************************************************/

			int iSpell = pLoopUnit->chooseSpell();
			if (iSpell != NO_SPELL)
			{
				pLoopUnit->cast(iSpell);
			}
		}
	}
	if (doDelayedDeath()) //Spells can kill units
	{
		return true;
	}
	return false;
}
/*************************************************************************************************/
/**	Improved spell usage					END													**/
/*************************************************************************************************/
/*************************************************************************************************/
/**	Tweak							05/05/11								Snarko				**/
/**			Making ranged attacks cost a movement point and adjusting the AI.					**/
/*************************************************************************************************/
bool CvSelectionGroupAI::AI_doRangedAttackPost()
{
	CvUnit* pLoopUnit;
	bool bRangedAttack = false;

	//Don't do this if we are for example healing.
	//AI doesn't do sleep, sentry or fortify.
	if (headMissionQueueNode() == NULL || headMissionQueueNode()->m_data.eMissionType == MISSION_SKIP)
	{
		for (int iI = 0; iI < getNumUnits(); iI++)
		{
			pLoopUnit = getUnitAt(iI);
			if (pLoopUnit->canMove())
			{
				if (pLoopUnit->AI_rangeAttack(pLoopUnit->airRange(), 101))
				{
					bRangedAttack = true;
				}
			}
		}
	}

	return bRangedAttack;
}
/*************************************************************************************************/
/**	Tweak									END													**/
/*************************************************************************************************/

// Returns true if the group has become busy...
bool CvSelectionGroupAI::AI_update()
{
	CLLNode<IDInfo>* pEntityNode;
	CvUnit* pLoopUnit;
	bool bDead;
	bool bFollow;

	PROFILE("CvSelectionGroupAI::AI_update");

	FAssert(getOwnerINLINE() != NO_PLAYER);

//FfH: Modified by Kael 12/28/2008
//	if (!AI_isControlled())
	if (!AI_isControlled() && !isAIControl())
//FfH: End Modify

	{
		return false;
	}

	if (getNumUnits() == 0)
	{
		return false;
	}

/************************************************************************************************/
/* BETTER_BTS_AI_MOD                      04/28/10                                jdog5000      */
/*                                                                                              */
/* Unit AI                                                                                      */
/************************************************************************************************/
	if( !(isHuman()) && !(getHeadUnit()->isCargo()) && getActivityType() == ACTIVITY_SLEEP )
	{
		setForceUpdate(true);
	}
/************************************************************************************************/
/* BETTER_BTS_AI_MOD                       END                                                  */
/************************************************************************************************/

	if (isForceUpdate())
	{
		clearMissionQueue(); // XXX ???
		setActivityType(ACTIVITY_AWAKE);
		setForceUpdate(false);

		// if we are in the middle of attacking with a stack, cancel it
		AI_cancelGroupAttack();
	}

	FAssert(!(GET_PLAYER(getOwnerINLINE()).isAutoMoves()));

	int iTempHack = 0; // XXX

	bDead = false;

	bool bFailedAlreadyFighting = false;
	while ((m_bGroupAttack && !bFailedAlreadyFighting) || readyToMove())
	{
		iTempHack++;
		if (iTempHack > 20)
		{
		//	FAssert(false);
			CvUnit* pHeadUnit = getHeadUnit();
			if (NULL != pHeadUnit)
			{
				if (GC.getLogging())
				{
					TCHAR szOut[1024];
					CvWString szTempString;
					getUnitAIString(szTempString, pHeadUnit->AI_getUnitAIType());
					sprintf(szOut, "Unit stuck in loop: %S(%S)[%d, %d] (%S)\n", pHeadUnit->getName().GetCString(), GET_PLAYER(pHeadUnit->getOwnerINLINE()).getName(),
						pHeadUnit->getX_INLINE(), pHeadUnit->getY_INLINE(), szTempString.GetCString());
					gDLL->messageControlLog(szOut);
				}

				pHeadUnit->finishMoves();
			}
			break;
		}

		// if we want to force the group to attack, force another attack
		if (m_bGroupAttack)
		{
			m_bGroupAttack = false;

			groupAttack(m_iGroupAttackX, m_iGroupAttackY, MOVE_DIRECT_ATTACK, bFailedAlreadyFighting);
		}
		// else pick AI action
		else
		{
			CvUnit* pHeadUnit = getHeadUnit();

			if (pHeadUnit == NULL || pHeadUnit->isDelayedDeath())
			{
				break;
			}

			resetPath();

			if (pHeadUnit->AI_update())
			{
				// AI_update returns true when we should abort the loop and wait until next slice
				break;
			}
		}

		if (doDelayedDeath())
		{
			bDead = true;
			break;
		}

		// if no longer group attacking, and force separate is true, then bail, decide what to do after group is split up
		// (UnitAI of head unit may have changed)
		if (!m_bGroupAttack && AI_isForceSeparate())
		{
			AI_separate();	// pointers could become invalid...
/*************************************************************************************************/
/**	Speedup								26/10/12										Snarko	**/
/**																								**/
/**			Imported from caveman2cosmos from K-mod						**/
/*************************************************************************************************/
/**								---- Start Original Code ----									**
			return true;
/**								----  End Original Code  ----									**/
			return false;
/*************************************************************************************************/
/**	Speedup									END													**/
/*************************************************************************************************/
		}
	}

	if (!bDead)
	{
		if (!isHuman())
		{
			bFollow = false;

			// if we not group attacking, then check for follow action
			if (!m_bGroupAttack)
			{
				pEntityNode = headUnitNode();

				while ((pEntityNode != NULL) && readyToMove(true))
				{
					pLoopUnit = ::getUnit(pEntityNode->m_data);
					pEntityNode = nextUnitNode(pEntityNode);

					if (pLoopUnit->canMove())
					{
						resetPath();

						if (pLoopUnit->AI_follow())
						{
							bFollow = true;
							break;
						}
					}
				}
			}

			if (doDelayedDeath())
			{
				bDead = true;
			}

			if (!bDead)
			{
				if (!bFollow && readyToMove(true))
				{
					pushMission(MISSION_SKIP);
				}
			}
		}
	}

	if (bDead)
	{
/*************************************************************************************************/
/**	Speedup								26/10/12										Snarko	**/
/**																								**/
/**			Imported from caveman2cosmos from K-mod						**/
/*************************************************************************************************/
/**								---- Start Original Code ----									**
		return true;
/**								----  End Original Code  ----									**/
		return false;
/*************************************************************************************************/
/**	Speedup									END													**/
/*************************************************************************************************/
	}

	return (isBusy() || isCargoBusy());
}


// Returns attack odds out of 100 (the higher, the better...)
int CvSelectionGroupAI::AI_attackOdds(const CvPlot* pPlot, bool bPotentialEnemy) const
{
	PROFILE_FUNC();

	CvUnit* pAttacker;

	FAssert(getOwnerINLINE() != NO_PLAYER);

/************************************************************************************************/
/* BETTER_BTS_AI_MOD                      02/21/10                                jdog5000      */
/*                                                                                              */
/* Efficiency, Lead From Behind                                                                 */
/************************************************************************************************/
	// From Lead From Behind by UncutDragon
	// original
	//if (pPlot->getBestDefender(NO_PLAYER, getOwnerINLINE(), NULL, !bPotentialEnemy, bPotentialEnemy) == NULL)
	// modified
	if (!pPlot->hasDefender(false, NO_PLAYER, getOwnerINLINE(), NULL, !bPotentialEnemy, bPotentialEnemy))
/************************************************************************************************/
/* BETTER_BTS_AI_MOD                       END                                                  */
/************************************************************************************************/
	{
		return 100;
	}

	int iOdds = 0;
	pAttacker = AI_getBestGroupAttacker(pPlot, bPotentialEnemy, iOdds);

	if (pAttacker == NULL)
	{
		return 0;
	}

	return iOdds;
}


CvUnit* CvSelectionGroupAI::AI_getBestGroupAttacker(const CvPlot* pPlot, bool bPotentialEnemy, int& iUnitOdds, bool bForce, bool bNoBlitz) const
{
	PROFILE_FUNC();

	CLLNode<IDInfo>* pUnitNode;
	CvUnit* pLoopUnit;
	CvUnit* pBestUnit;
	int iPossibleTargets;
	int iValue;
	int iBestValue;
	int iOdds;
	int iBestOdds;

	iBestValue = 0;
	iBestOdds = 0;
	pBestUnit = NULL;

	pUnitNode = headUnitNode();

	bool bIsHuman = (pUnitNode != NULL) ? GET_PLAYER(::getUnit(pUnitNode->m_data)->getOwnerINLINE()).isHuman() : true;

	while (pUnitNode != NULL)
	{
		pLoopUnit = ::getUnit(pUnitNode->m_data);
		pUnitNode = nextUnitNode(pUnitNode);

		if (!pLoopUnit->isDead())
		{
			bool bCanAttack = false;
			if (pLoopUnit->getDomainType() == DOMAIN_AIR)
			{
				bCanAttack = pLoopUnit->canAirAttack();
			}
			else
			{
				bCanAttack = pLoopUnit->canAttack();

				if (bCanAttack && bNoBlitz && pLoopUnit->isBlitz() && pLoopUnit->isMadeAttack())
				{
					bCanAttack = false;
				}
			}

			if (bCanAttack)
			{
				if (bForce || pLoopUnit->canMove())
				{
					if (bForce || pLoopUnit->canMoveInto(pPlot, /*bAttack*/ true, /*bDeclareWar*/ bPotentialEnemy))
					{
/************************************************************************************************/
/* BETTER_BTS_AI_MOD                      02/21/10                                jdog5000      */
/*                                                                                              */
/* Lead From Behind                                                                             */
/************************************************************************************************/
						// From Lead From Behind by UncutDragon
						if (GC.getLFBEnable() && GC.getLFBUseCombatOdds())
						{
							pLoopUnit->LFBgetBetterAttacker(&pBestUnit, pPlot, bPotentialEnemy, iBestOdds, iValue);
						}
						else
						{
							iOdds = pLoopUnit->AI_attackOdds(pPlot, bPotentialEnemy);

							iValue = iOdds;
							FAssertMsg(iValue > 0, "iValue is expected to be greater than 0");

							if (pLoopUnit->collateralDamage() > 0)
							{
								iPossibleTargets = std::min((pPlot->getNumVisibleEnemyDefenders(pLoopUnit) - 1), pLoopUnit->collateralDamageMaxUnits());

								if (iPossibleTargets > 0)
								{
									iValue *= (100 + ((pLoopUnit->collateralDamage() * iPossibleTargets) / 5));
									iValue /= 100;
								}
							}

							// if non-human, prefer the last unit that has the best value (so as to avoid splitting the group)
							if (iValue > iBestValue || (!bIsHuman && iValue > 0 && iValue == iBestValue))
							{
								iBestValue = iValue;
								iBestOdds = iOdds;
								pBestUnit = pLoopUnit;
							}
						}
/************************************************************************************************/
/* BETTER_BTS_AI_MOD                       END                                                  */
/************************************************************************************************/
					}
				}
			}
		}
	}

	iUnitOdds = iBestOdds;
	return pBestUnit;
}

CvUnit* CvSelectionGroupAI::AI_getBestGroupSacrifice(const CvPlot* pPlot, bool bPotentialEnemy, bool bForce, bool bNoBlitz) const
{
	PROFILE_FUNC();

	int iBestValue = 0;
	CvUnit* pBestUnit = NULL;

	CLLNode<IDInfo>* pUnitNode = headUnitNode();
	while (pUnitNode != NULL)
	{
		CvUnit* pLoopUnit = ::getUnit(pUnitNode->m_data);
		pUnitNode = nextUnitNode(pUnitNode);

		if (!pLoopUnit->isDead())
		{
			bool bCanAttack = false;
			if (pLoopUnit->getDomainType() == DOMAIN_AIR)
			{
				bCanAttack = pLoopUnit->canAirAttack();
			}
			else
			{
				bCanAttack = pLoopUnit->canAttack();

				if (bCanAttack && bNoBlitz && pLoopUnit->isBlitz() && pLoopUnit->isMadeAttack())
				{
					bCanAttack = false;
				}
			}

			if (bCanAttack)
			{
				if (bForce || pLoopUnit->canMove())
				{
					if (bForce || pLoopUnit->canMoveInto(pPlot, true))
					{
						int iValue = pLoopUnit->AI_sacrificeValue(pPlot);
						FAssertMsg(iValue > 0, "iValue is expected to be greater than 0");

						// we want to pick the last unit of highest value, so pick the last unit with a good value
						if (iValue >= iBestValue)
						{
							iBestValue = iValue;
							pBestUnit = pLoopUnit;
						}
					}
				}
			}
		}
	}

	return pBestUnit;
}

// Returns ratio of strengths of stacks times 100
// (so 100 is even ratio, numbers over 100 mean this group is more powerful than the stack on a plot)
int CvSelectionGroupAI::AI_compareStacks(const CvPlot* pPlot, bool bPotentialEnemy, bool bCheckCanAttack, bool bCheckCanMove) const
{
	FAssert(pPlot != NULL);

	int	compareRatio;
	DomainTypes eDomainType = getDomainType();

	// if not aircraft, then choose based on the plot, not the head unit (mainly for transport carried units)
	if (eDomainType != DOMAIN_AIR)
	{
		if (pPlot->isWater())
			eDomainType = DOMAIN_SEA;
		else
			eDomainType = DOMAIN_LAND;

	}

	compareRatio = AI_sumStrength(pPlot, eDomainType, bCheckCanAttack, bCheckCanMove);
	compareRatio *= 100;

	PlayerTypes eOwner = getOwnerINLINE();
	if (eOwner == NO_PLAYER)
	{
		eOwner = getHeadOwner();
	}
	FAssert(eOwner != NO_PLAYER);

/************************************************************************************************/
/* UNOFFICIAL_PATCH                       03/04/10                                jdog5000      */
/*                                                                                              */
/* Bugfix                                                                                       */
/************************************************************************************************/
/* original bts code
	int defenderSum = pPlot->AI_sumStrength(NO_PLAYER, getOwnerINLINE(), eDomainType, true, !bPotentialEnemy, bPotentialEnemy);
*/
	// Clearly meant to use eOwner here ...
	int defenderSum = pPlot->AI_sumStrength(NO_PLAYER, eOwner, eDomainType, true, !bPotentialEnemy, bPotentialEnemy);
/************************************************************************************************/
/* UNOFFICIAL_PATCH                        END                                                  */
/************************************************************************************************/
	compareRatio /= std::max(1, defenderSum);

	return compareRatio;
}

int CvSelectionGroupAI::AI_sumStrength(const CvPlot* pAttackedPlot, DomainTypes eDomainType, bool bCheckCanAttack, bool bCheckCanMove) const
{
	CLLNode<IDInfo>* pUnitNode;
	CvUnit* pLoopUnit;
	int	strSum = 0;

	pUnitNode = headUnitNode();

	while (pUnitNode != NULL)
	{
		pLoopUnit = ::getUnit(pUnitNode->m_data);
		pUnitNode = nextUnitNode(pUnitNode);

		if (!pLoopUnit->isDead())
		{
			bool bCanAttack = false;
			if (pLoopUnit->getDomainType() == DOMAIN_AIR)
				bCanAttack = pLoopUnit->canAirAttack();
			else
				bCanAttack = pLoopUnit->canAttack();

			if (!bCheckCanAttack || bCanAttack)
			{
				if (!bCheckCanMove || pLoopUnit->canMove())
					if (!bCheckCanMove || pAttackedPlot == NULL || pLoopUnit->canMoveInto(pAttackedPlot, /*bAttack*/ true, /*bDeclareWar*/ true))
						if (eDomainType == NO_DOMAIN || pLoopUnit->getDomainType() == eDomainType)
							strSum += pLoopUnit->currEffectiveStr(pAttackedPlot, pLoopUnit);
			}
		}
	}

	return strSum;
}

void CvSelectionGroupAI::AI_queueGroupAttack(int iX, int iY)
{
	m_bGroupAttack = true;

	m_iGroupAttackX = iX;
	m_iGroupAttackY = iY;
}

inline void CvSelectionGroupAI::AI_cancelGroupAttack()
{
	m_bGroupAttack = false;
}

inline bool CvSelectionGroupAI::AI_isGroupAttack()
{
	return m_bGroupAttack;
}

bool CvSelectionGroupAI::AI_isControlled()
{
	return (!isHuman() || isAutomated());
}


bool CvSelectionGroupAI::AI_isDeclareWar(const CvPlot* pPlot)
{
	FAssert(getHeadUnit() != NULL);

	if (isHuman())
	{
		return false;
	}
	else
	{
		bool bLimitedWar = false;
		if (pPlot != NULL)
		{
			TeamTypes ePlotTeam = pPlot->getTeam();
			if (ePlotTeam != NO_TEAM)
			{
				WarPlanTypes eWarplan = GET_TEAM(getTeam()).AI_getWarPlan(ePlotTeam);
				if (eWarplan == WARPLAN_LIMITED)
				{
					bLimitedWar = true;
				}
			}
		}

		CvUnit* pHeadUnit = getHeadUnit();

		if (pHeadUnit != NULL)
		{
			switch (pHeadUnit->AI_getUnitAIType())
			{
			case UNITAI_UNKNOWN:
			case UNITAI_ANIMAL:
			case UNITAI_SETTLE:
			case UNITAI_WORKER:
				break;
			case UNITAI_ATTACK_CITY:
			case UNITAI_ATTACK_CITY_LEMMING:
				return true;
				break;

			case UNITAI_ATTACK:
			case UNITAI_COLLATERAL:
			case UNITAI_PILLAGE:
				if (bLimitedWar)
				{
					return true;
				}
				break;

			case UNITAI_PARADROP:
			case UNITAI_RESERVE:
			case UNITAI_COUNTER:
			case UNITAI_CITY_DEFENSE:
			case UNITAI_CITY_COUNTER:
			case UNITAI_CITY_SPECIAL:
			case UNITAI_EXPLORE:
			case UNITAI_MISSIONARY:
			case UNITAI_PROPHET:
			case UNITAI_ARTIST:
			case UNITAI_SCIENTIST:
			case UNITAI_GENERAL:
			case UNITAI_MERCHANT:
			case UNITAI_ENGINEER:
			case UNITAI_SPY:
			case UNITAI_ICBM:
			case UNITAI_WORKER_SEA:
				break;

			case UNITAI_ATTACK_SEA:
			case UNITAI_RESERVE_SEA:
			case UNITAI_ESCORT_SEA:
				if (bLimitedWar)
				{
					return true;
				}
				break;
			case UNITAI_EXPLORE_SEA:
				break;

			case UNITAI_ASSAULT_SEA:
				if (hasCargo())
				{
					return true;
				}
				break;

			case UNITAI_SETTLER_SEA:
			case UNITAI_MISSIONARY_SEA:
			case UNITAI_SPY_SEA:
			case UNITAI_CARRIER_SEA:
			case UNITAI_MISSILE_CARRIER_SEA:
			case UNITAI_PIRATE_SEA:
			case UNITAI_ATTACK_AIR:
			case UNITAI_DEFENSE_AIR:
			case UNITAI_CARRIER_AIR:
			case UNITAI_MISSILE_AIR:
				break;
			case UNITAI_WARWIZARD:
			case UNITAI_HERO:
			case UNITAI_FEASTING:
				return true;
				break;
			case UNITAI_MAGE:
			case UNITAI_MANA_UPGRADE:
			case UNITAI_TERRAFORMER:
			case UNITAI_FORT_COMMANDER:
			case UNITAI_HEALER:
			case UNITAI_MEDIC:
				break;

			default:
				FAssert(false);
				break;
			}
		}
	}

	return false;
}


CvPlot* CvSelectionGroupAI::AI_getMissionAIPlot()
{
	return GC.getMapINLINE().plotSorenINLINE(m_iMissionAIX, m_iMissionAIY);
}


bool CvSelectionGroupAI::AI_isForceSeparate()
{
	return m_bForceSeparate;
}


void CvSelectionGroupAI::AI_makeForceSeparate()
{
	m_bForceSeparate = true;
}

/*************************************************************************************************/
/**	K-mod merger								16/02/12								Snarko	**/
/**																								**/
/**					Merging in features of K-mod, most notably the pathfinder					**/
/*************************************************************************************************/
/**								---- Start Original Code ----									**
MissionAITypes CvSelectionGroupAI::AI_getMissionAIType()
/**								----  End Original Code  ----									**/
MissionAITypes CvSelectionGroupAI::AI_getMissionAIType() const
/*************************************************************************************************/
/**	K-mod merger								END												**/
/*************************************************************************************************/
{
	return m_eMissionAIType;
}


void CvSelectionGroupAI::AI_setMissionAI(MissionAITypes eNewMissionAI, CvPlot* pNewPlot, CvUnit* pNewUnit)
{
	m_eMissionAIType = eNewMissionAI;

	if (pNewPlot != NULL)
	{
		m_iMissionAIX = pNewPlot->getX_INLINE();
		m_iMissionAIY = pNewPlot->getY_INLINE();
	}
	else
	{
		m_iMissionAIX = INVALID_PLOT_COORD;
		m_iMissionAIY = INVALID_PLOT_COORD;
	}

	if (pNewUnit != NULL)
	{
		m_missionAIUnit = pNewUnit->getIDInfo();
	}
	else
	{
		m_missionAIUnit.reset();
	}
}


CvUnit* CvSelectionGroupAI::AI_getMissionAIUnit()
{
	return getUnit(m_missionAIUnit);
}

bool CvSelectionGroupAI::AI_isFull()
{
	CLLNode<IDInfo>* pUnitNode;
	CvUnit* pLoopUnit;

	if (getNumUnits() > 0)
	{
		UnitAITypes eUnitAI = getHeadUnitAI();
		// do two passes, the first pass, we ignore units with speical cargo
		int iSpecialCargoCount = 0;
		int iCargoCount = 0;

		// first pass, count but ignore special cargo units
		pUnitNode = headUnitNode();

		while (pUnitNode != NULL)
		{
			pLoopUnit = ::getUnit(pUnitNode->m_data);
			pUnitNode = nextUnitNode(pUnitNode);
			if (pLoopUnit->AI_getUnitAIType() == eUnitAI)
			{
				if (pLoopUnit->cargoSpace() > 0)
				{
					iCargoCount++;
				}

				if (pLoopUnit->specialCargo() != NO_SPECIALUNIT)
				{
					iSpecialCargoCount++;
				}
				else if (!(pLoopUnit->isFull()))
				{
					return false;
				}
			}
		}

		// if every unit in the group has special cargo, then check those, otherwise, consider ourselves full
		if (iSpecialCargoCount >= iCargoCount)
		{
			pUnitNode = headUnitNode();
			while (pUnitNode != NULL)
			{
				pLoopUnit = ::getUnit(pUnitNode->m_data);
				pUnitNode = nextUnitNode(pUnitNode);

				if (pLoopUnit->AI_getUnitAIType() == eUnitAI)
				{
					if (!(pLoopUnit->isFull()))
					{
						return false;
					}
				}
			}
		}

		return true;
	}

	return false;
}


CvUnit* CvSelectionGroupAI::AI_ejectBestDefender(CvPlot* pDefendPlot)
{
	CLLNode<IDInfo>* pEntityNode;
	CvUnit* pLoopUnit;

	pEntityNode = headUnitNode();

	CvUnit* pBestUnit = NULL;
	int iBestUnitValue = 0;

	while (pEntityNode != NULL)
	{
		pLoopUnit = ::getUnit(pEntityNode->m_data);
		pEntityNode = nextUnitNode(pEntityNode);

		if (!pLoopUnit->noDefensiveBonus())
		{
			int iValue = pLoopUnit->currEffectiveStr(pDefendPlot, NULL) * 100;

			if (pDefendPlot->isCity(true, getTeam()))
			{
				iValue *= 100 + pLoopUnit->cityDefenseModifier();
				iValue /= 100;
			}

			iValue *= 100;
/*************************************************************************************************/
/**	Tweak					 	   10/04/10									Snarko				**/
/**																								**/
/**					Fixes a CtD with units that has -100% city attack modifiers					**/
/*************************************************************************************************/
/**								---- Start Original Code ----									**
			iValue /= (100 + pLoopUnit->cityAttackModifier() + pLoopUnit->getExtraCityAttackPercent());
/**								----  End Original Code  ----									**/
			iValue /= std::max(1, (100 + pLoopUnit->cityAttackModifier() + pLoopUnit->getExtraCityAttackPercent()));
/*************************************************************************************************/
/**	Tweak								END														**/
/*************************************************************************************************/

			iValue /= 2 + pLoopUnit->getLevel();

			if (iValue > iBestUnitValue)
			{
				iBestUnitValue = iValue;
				pBestUnit = pLoopUnit;
			}
		}
	}

	if (NULL != pBestUnit && getNumUnits() > 1)
	{
		pBestUnit->joinGroup(NULL);
	}

	return pBestUnit;
}


// Protected Functions...

void CvSelectionGroupAI::read(FDataStreamBase* pStream)
{
	CvSelectionGroup::read(pStream);

	uint uiFlag=0;
	pStream->Read(&uiFlag);	// flags for expansion

	pStream->Read(&m_iMissionAIX);
	pStream->Read(&m_iMissionAIY);

	pStream->Read(&m_bForceSeparate);

	pStream->Read((int*)&m_eMissionAIType);

	pStream->Read((int*)&m_missionAIUnit.eOwner);
	pStream->Read(&m_missionAIUnit.iID);

	pStream->Read(&m_bGroupAttack);
	pStream->Read(&m_iGroupAttackX);
	pStream->Read(&m_iGroupAttackY);
}


void CvSelectionGroupAI::write(FDataStreamBase* pStream)
{
	CvSelectionGroup::write(pStream);

	uint uiFlag=0;
	pStream->Write(uiFlag);		// flag for expansion

	pStream->Write(m_iMissionAIX);
	pStream->Write(m_iMissionAIY);

	pStream->Write(m_bForceSeparate);

	pStream->Write(m_eMissionAIType);

	pStream->Write(m_missionAIUnit.eOwner);
	pStream->Write(m_missionAIUnit.iID);

	pStream->Write(m_bGroupAttack);
	pStream->Write(m_iGroupAttackX);
	pStream->Write(m_iGroupAttackY);
}

// Private Functions...
