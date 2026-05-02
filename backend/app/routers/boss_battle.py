from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.schemas import ApiResponse
from app.services.boss_battle_service import (
    get_boss_battle_service,
    BossBattleService,
    BossStatus,
    TeamStatus,
    ELEMENTS,
    ELEMENT_SYMBOLS,
    ELEMENT_COLORS
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["星象BOSS副本"])

boss_service = get_boss_battle_service()


class CreateTeamRequest(BaseModel):
    boss_id: str = Field(..., description="BOSS ID")
    team_name: Optional[str] = Field("星之队", description="队伍名称")
    leader_data: Dict[str, Any] = Field(..., description="队长数据，包含member_id, name, element, combat_power, stats, passives等")


class AddMemberRequest(BaseModel):
    team_id: str = Field(..., description="队伍ID")
    member_data: Dict[str, Any] = Field(..., description="成员数据")


class InviteToTeamRequest(BaseModel):
    encounter_session_id: Optional[str] = Field(None, description="偶遇会话ID")
    boss_id: str = Field(..., description="目标BOSS ID")
    team_name: Optional[str] = Field("星之队", description="队伍名称")
    inviter_data: Dict[str, Any] = Field(..., description="邀请者数据")
    invitee_data: Dict[str, Any] = Field(..., description="被邀请者数据")


class StartBattleRequest(BaseModel):
    team_id: str = Field(..., description="队伍ID")


@router.get("/hall", response_model=ApiResponse)
async def get_boss_hall():
    """
    获取副本大厅信息
    - 当前活跃的BOSS列表
    - 各BOSS的组队需求
    - 整体活动状态
    """
    try:
        active_bosses = boss_service.get_active_bosses()
        
        boss_list = []
        for boss in active_bosses:
            teams = boss_service.get_teams_by_boss(boss.boss_id)
            recruiting_teams = [t for t in teams if t.status in [TeamStatus.RECRUITING, TeamStatus.READY]]
            
            boss_dict = boss_service._boss_to_dict(boss)
            boss_dict["team_count"] = len(teams)
            boss_dict["recruiting_teams"] = [
                boss_service._team_to_dict(t) for t in recruiting_teams
            ]
            boss_dict["required_elements"] = ELEMENTS
            boss_dict["element_symbols"] = ELEMENT_SYMBOLS
            boss_list.append(boss_dict)
        
        current_events = boss_service._detect_current_transit_events()
        
        result = {
            "active_bosses": boss_list,
            "current_transit_events": current_events,
            "element_info": {
                "elements": ELEMENTS,
                "symbols": ELEMENT_SYMBOLS,
                "colors": ELEMENT_COLORS
            },
            "hall_status": "active"
        }
        
        return ApiResponse(
            message="获取副本大厅信息成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取副本大厅信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取副本大厅信息失败: {str(e)}"
        )


@router.get("/bosses", response_model=ApiResponse)
async def get_active_bosses():
    """获取当前活跃的BOSS列表"""
    try:
        bosses = boss_service.get_active_bosses()
        
        result = {
            "bosses": [boss_service._boss_to_dict(b) for b in bosses],
            "count": len(bosses)
        }
        
        return ApiResponse(
            message="获取BOSS列表成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取BOSS列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取BOSS列表失败: {str(e)}"
        )


@router.get("/bosses/{boss_id}", response_model=ApiResponse)
async def get_boss_detail(boss_id: str):
    """获取BOSS详细信息"""
    try:
        boss = boss_service.get_boss_by_id(boss_id)
        if not boss:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"BOSS不存在: {boss_id}"
            )
        
        teams = boss_service.get_teams_by_boss(boss_id)
        
        result = {
            "boss": boss_service._boss_to_dict(boss),
            "teams": [boss_service._team_to_dict(t) for t in teams],
            "team_count": len(teams)
        }
        
        return ApiResponse(
            message="获取BOSS详情成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取BOSS详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取BOSS详情失败: {str(e)}"
        )


@router.post("/teams/create", response_model=ApiResponse)
async def create_team(request: CreateTeamRequest):
    """
    创建队伍
    - 基于偶遇后邀请组队时调用
    - 队长信息需要包含: member_id, name, element, combat_power, stats, passives
    """
    try:
        boss = boss_service.get_boss_by_id(request.boss_id)
        if not boss:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"BOSS不存在: {request.boss_id}"
            )
        
        required_fields = ["member_id", "name", "element", "combat_power"]
        for field in required_fields:
            if field not in request.leader_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"缺少必要字段: {field}"
                )
        
        team = boss_service.create_team(
            boss_id=request.boss_id,
            leader_data=request.leader_data,
            team_name=request.team_name or "星之队"
        )
        
        if not team:
            member_id = request.leader_data.get("member_id")
            existing_team = boss_service.get_member_current_team(member_id)
            if existing_team:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"用户已在其他队伍中，队伍ID: {existing_team.get('team_id')}"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建队伍失败"
            )
        
        return ApiResponse(
            message="创建队伍成功",
            data=boss_service._team_to_dict(team)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建队伍失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建队伍失败: {str(e)}"
        )


@router.post("/teams/invite-from-encounter", response_model=ApiResponse)
async def invite_from_encounter(request: InviteToTeamRequest):
    """
    从偶遇中邀请组队（原子化操作）
    - 这是广场偶遇后的「邀请组队」按钮调用的接口
    - 将偶遇的双方加入同一个队伍，确保要么都加入，要么都不加入
    """
    try:
        boss = boss_service.get_boss_by_id(request.boss_id)
        if not boss:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"BOSS不存在: {request.boss_id}"
            )
        
        required_fields = ["member_id", "name", "element", "combat_power"]
        
        for field in required_fields:
            if field not in request.inviter_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"邀请者数据缺少必要字段: {field}"
                )
            if field not in request.invitee_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"被邀请者数据缺少必要字段: {field}"
                )
        
        result = boss_service.invite_from_encounter_atomic(
            boss_id=request.boss_id,
            inviter_data=request.inviter_data,
            invitee_data=request.invitee_data,
            team_name=request.team_name or "星之队"
        )
        
        if not result.get("success"):
            error = result.get("error", "邀请组队失败")
            
            if result.get("duplicate_member"):
                member_type = result.get("member_type", "未知")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{member_type}已在其他队伍中，请先离开当前队伍"
                )
            
            if result.get("duplicate_element"):
                conflict_element = result.get("conflict_element", "未知")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"元素冲突：双方都是 {conflict_element} 象，不能加入同一队伍。队伍中每种元素只能有一名成员。"
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return ApiResponse(
            message="邀请组队成功",
            data={
                "team": result.get("team"),
                "encounter_session_id": request.encounter_session_id,
                "members_added": result.get("members_added", 2)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"邀请组队失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"邀请组队失败: {str(e)}"
        )


@router.post("/teams/add-member", response_model=ApiResponse)
async def add_team_member(request: AddMemberRequest):
    """添加成员到队伍（线程安全）"""
    try:
        result = boss_service.add_member_to_team(
            team_id=request.team_id,
            member_data=request.member_data
        )
        
        if not result.get("success"):
            error = result.get("error", "添加成员失败")
            
            if result.get("duplicate_member"):
                other_team = result.get("other_team")
                if other_team:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"用户已在队伍 {other_team} 中，请先离开当前队伍"
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户已在当前队伍中"
                )
            
            if result.get("team_full"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="队伍已满（最多4人）"
                )
            
            if result.get("duplicate_element"):
                conflict_element = result.get("conflict_element", "未知")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"元素冲突：队伍中已存在 {conflict_element} 象成员。队伍中每种元素只能有一名成员。"
                )
            
            if result.get("team_not_found"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="队伍不存在"
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return ApiResponse(
            message="添加成员成功",
            data=result.get("team")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加成员失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加成员失败: {str(e)}"
        )


@router.delete("/teams/{team_id}/members/{member_id}", response_model=ApiResponse)
async def remove_team_member(team_id: str, member_id: str):
    """从队伍移除成员"""
    try:
        result = boss_service.remove_member_from_team(team_id, member_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "移除成员失败")
            )
        
        return ApiResponse(
            message="移除成员成功",
            data={
                "team": result.get("team"),
                "team_disbanded": result.get("team_disbanded", False)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除成员失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除成员失败: {str(e)}"
        )


@router.post("/teams/leave", response_model=ApiResponse)
async def leave_current_team(member_id: str):
    """
    用户离开当前队伍
    """
    try:
        result = boss_service.leave_team(member_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "离开队伍失败")
            )
        
        return ApiResponse(
            message="离开队伍成功",
            data={
                "team": result.get("team"),
                "team_disbanded": result.get("team_disbanded", False)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"离开队伍失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"离开队伍失败: {str(e)}"
        )


@router.get("/teams/member/{member_id}/current", response_model=ApiResponse)
async def get_member_current_team(member_id: str):
    """
    获取用户当前所在的队伍
    """
    try:
        team = boss_service.get_member_current_team(member_id)
        
        return ApiResponse(
            message="获取用户队伍信息成功",
            data={
                "has_team": team is not None,
                "team": team
            }
        )
        
    except Exception as e:
        logger.error(f"获取用户队伍信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户队伍信息失败: {str(e)}"
        )


@router.get("/teams/{team_id}", response_model=ApiResponse)
async def get_team_detail(team_id: str):
    """获取队伍详细信息"""
    try:
        team = boss_service.get_team_by_id(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"队伍不存在: {team_id}"
            )
        
        boss = boss_service.get_boss_by_id(team.boss_id)
        
        team_dict = boss_service._team_to_dict(team)
        
        result = {
            "team": team_dict,
            "boss": boss_service._boss_to_dict(boss) if boss else None,
            "can_start_battle": team_dict.get("has_all_elements", False) and team.status == TeamStatus.READY
        }
        
        return ApiResponse(
            message="获取队伍详情成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取队伍详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取队伍详情失败: {str(e)}"
        )


@router.post("/battle/start", response_model=ApiResponse)
async def start_battle(request: StartBattleRequest, background_tasks: BackgroundTasks):
    """
    开始战斗（异步非阻塞）
    - 先返回战斗ID，后台异步生成AI史诗剧情
    - 解决接口超时问题
    """
    try:
        result = await boss_service.start_battle_async(request.team_id)
        
        if not result.get("success"):
            error = result.get("error", "开始战斗失败")
            
            if not result.get("has_all_elements"):
                missing = result.get("missing_elements", [])
                missing_with_symbols = [f"{ELEMENT_SYMBOLS.get(e, '❓')}{e}" for e in missing]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"队伍元素不完整，缺少: {', '.join(missing_with_symbols)}。需要包含火、土、风、水四种元素才能开战。"
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        battle_id = result.get("battle_id")
        if battle_id:
            background_tasks.add_task(boss_service.trigger_battle_background, battle_id)
        
        return ApiResponse(
            message="战斗已开始",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始战斗失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始战斗失败: {str(e)}"
        )


@router.get("/battle/result/{battle_id}", response_model=ApiResponse)
async def get_battle_result(battle_id: str):
    """
    获取战斗结果
    - 用于轮询异步战斗的结果
    """
    try:
        result = boss_service.get_battle_result(battle_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"战斗不存在: {battle_id}"
            )
        
        if result.get("status") == "processing":
            return ApiResponse(
                message="战斗进行中",
                data={
                    "battle_id": battle_id,
                    "status": "processing",
                    "message": result.get("message", "战斗正在进行中...")
                }
            )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "战斗执行失败")
            )
        
        return ApiResponse(
            message="获取战斗结果成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取战斗结果失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取战斗结果失败: {str(e)}"
        )


@router.get("/teams/by-boss/{boss_id}", response_model=ApiResponse)
async def get_teams_by_boss(boss_id: str):
    """获取指定BOSS的所有队伍"""
    try:
        boss = boss_service.get_boss_by_id(boss_id)
        if not boss:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"BOSS不存在: {boss_id}"
            )
        
        teams = boss_service.get_teams_by_boss(boss_id)
        
        result = {
            "boss": boss_service._boss_to_dict(boss),
            "teams": [boss_service._team_to_dict(t) for t in teams],
            "count": len(teams)
        }
        
        return ApiResponse(
            message="获取队伍列表成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取队伍列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取队伍列表失败: {str(e)}"
        )


@router.get("/match/auto-match/{boss_id}", response_model=ApiResponse)
async def auto_match_for_boss(boss_id: str, element: Optional[str] = None):
    """
    自动匹配
    - 查找满足元素条件的在线用户
    - 可以按元素需求匹配
    """
    try:
        boss = boss_service.get_boss_by_id(boss_id)
        if not boss:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"BOSS不存在: {boss_id}"
            )
        
        teams = boss_service.get_teams_by_boss(boss_id)
        
        recruiting_teams = []
        for team in teams:
            if team.status in [TeamStatus.RECRUITING, TeamStatus.READY]:
                team_dict = boss_service._team_to_dict(team)
                if element:
                    if element not in team.elements_present:
                        recruiting_teams.append(team_dict)
                else:
                    recruiting_teams.append(team_dict)
        
        result = {
            "boss": boss_service._boss_to_dict(boss),
            "available_teams": recruiting_teams,
            "match_recommendations": [
                {
                    "type": "join_team",
                    "description": "加入现有队伍",
                    "teams": recruiting_teams[:5]
                },
                {
                    "type": "create_team",
                    "description": "创建新队伍",
                    "required_elements": ELEMENTS
                }
            ]
        }
        
        return ApiResponse(
            message="获取匹配信息成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"自动匹配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自动匹配失败: {str(e)}"
        )
