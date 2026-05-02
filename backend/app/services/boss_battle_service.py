import logging
import json
import random
import threading
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from app.services.ai_service import call_deepseek_api
from app.services.transit_service import (
    get_transit_analysis_engine,
    TransitAnalysisEngine,
    calculate_moon_phase,
    check_mercury_retrograde
)
from app.services.ephemeris_calculator import get_ephemeris_calculator
from app.astro import MAIN_PLANETS

logger = logging.getLogger(__name__)

transit_engine = get_transit_analysis_engine()
ephemeris = get_ephemeris_calculator()


class BossStatus(str, Enum):
    SPAWNED = "spawned"
    ACTIVE = "active"
    FIGHTING = "fighting"
    VANQUISHED = "vanquished"
    ESCAPED = "escaped"


class TeamStatus(str, Enum):
    RECRUITING = "recruiting"
    READY = "ready"
    FIGHTING = "fighting"
    VICTORIOUS = "victorious"
    DEFEATED = "defeated"


ELEMENTS = ["火", "土", "风", "水"]
ELEMENT_COLORS = {
    "火": "#EF4444",
    "土": "#92400E",
    "风": "#059669",
    "水": "#2563EB"
}
ELEMENT_SYMBOLS = {
    "火": "🔥",
    "土": "🪨",
    "风": "🌪️",
    "水": "💧"
}


@dataclass
class BossSkill:
    skill_id: str
    name: str
    description: str
    element: str
    base_damage: int
    cooldown: int
    current_cooldown: int = 0
    is_ultimate: bool = False


@dataclass
class AstroBoss:
    boss_id: str
    name: str
    title: str
    boss_type: str
    trigger_event: str
    planet_involved: Optional[str]
    zodiac_sign: Optional[str]
    
    description: str
    lore: str
    
    max_health: int
    current_health: int
    base_power: int
    current_power: int
    
    weakness_element: str
    resistance_element: str
    
    fluctuation_value: int
    skills: List[BossSkill]
    
    status: BossStatus = BossStatus.SPAWNED
    spawned_at: datetime = field(default_factory=datetime.now)
    estimated_end_at: Optional[datetime] = None
    
    total_damage_received: int = 0
    participant_count: int = 0


@dataclass
class TeamMember:
    member_id: str
    name: str
    element: str
    combat_power: int
    stats: Dict[str, Any]
    passives: List[Dict[str, Any]]
    avatar_data: Dict[str, Any]
    
    is_leader: bool = False
    energy_contributed: int = 0


@dataclass
class BossTeam:
    team_id: str
    boss_id: str
    leader_id: str
    team_name: str
    
    members: List[TeamMember] = field(default_factory=list)
    elements_present: List[str] = field(default_factory=list)
    
    status: TeamStatus = TeamStatus.RECRUITING
    total_energy: int = 0
    
    damage_contributed: int = 0
    rewards_earned: Optional[Dict[str, Any]] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    battle_started_at: Optional[datetime] = None
    battle_ended_at: Optional[datetime] = None
    
    def add_member(self, member: TeamMember) -> bool:
        for m in self.members:
            if m.member_id == member.member_id:
                return False
        
        if len(self.members) >= 4:
            return False
        
        if member.element in self.elements_present:
            return False
        
        self.members.append(member)
        
        if member.element not in self.elements_present:
            self.elements_present.append(member.element)
        
        self._update_total_energy()
        self._check_ready_status()
        
        return True
    
    def remove_member(self, member_id: str) -> bool:
        for i, m in enumerate(self.members):
            if m.member_id == member_id:
                if m.is_leader and len(self.members) > 1:
                    self.members[1].is_leader = True
                self.members.pop(i)
                self._update_elements_present()
                self._update_total_energy()
                self._check_ready_status()
                return True
        return False
    
    def _update_elements_present(self):
        self.elements_present = list(set(m.element for m in self.members))
    
    def _update_total_energy(self):
        self.total_energy = sum(m.combat_power for m in self.members)
        for m in self.members:
            self.total_energy += int(m.stats.get("fire_power", 0) * 0.1)
            self.total_energy += int(m.stats.get("earth_power", 0) * 0.1)
            self.total_energy += int(m.stats.get("air_power", 0) * 0.1)
            self.total_energy += int(m.stats.get("water_power", 0) * 0.1)
    
    def _check_ready_status(self):
        if self.has_all_elements():
            self.status = TeamStatus.READY
        else:
            self.status = TeamStatus.RECRUITING
    
    def has_all_elements(self) -> bool:
        return set(ELEMENTS).issubset(set(self.elements_present))
    
    def get_missing_elements(self) -> List[str]:
        return [e for e in ELEMENTS if e not in self.elements_present]


class BossBattleService:
    """
    星象BOSS战斗服务
    - 基于实时天象生成BOSS
    - 管理BOSS战斗实例
    - 计算队伍能量与BOSS波动值对比
    - 调用DeepSeek生成战斗剧情
    - 计算奖励
    """
    
    def __init__(self):
        self.active_bosses: Dict[str, AstroBoss] = {}
        self.active_teams: Dict[str, BossTeam] = {}
        self.boss_spawn_history: List[Dict[str, Any]] = []
        
        self._lock = threading.RLock()
        self._member_team_map: Dict[str, str] = {}
        self._battle_results: Dict[str, Dict[str, Any]] = {}
        self._pending_battles: Dict[str, Dict[str, Any]] = {}
        
        self._setup_boss_templates()
        self._load_or_spawn_initial_boss()
    
    def _setup_boss_templates(self):
        """设置BOSS模板，基于不同的天象事件"""
        self.boss_templates = {
            "mercury_retrograde": {
                "name": "墨丘利的幽灵",
                "title": "通信之神的逆反",
                "boss_type": "transit_boss",
                "trigger_event": "mercury_retrograde",
                "planet_involved": "水星",
                "zodiac_sign": None,
                "description": "水星逆行期间，沟通之神墨丘利的能量变得混乱和逆反。电子设备故障、误解频发、旅行计划被打乱。",
                "lore": "在占星学中，水星掌管沟通、思维、旅行和商业。当水星逆行时，这些领域会变得混乱。传说中，每一次水星逆行都是墨丘利在测试人类的耐心和适应能力。",
                "base_health": 5000,
                "base_power": 150,
                "weakness_element": "土",
                "resistance_element": "风",
                "base_fluctuation": 60,
                "skills": [
                    {
                        "skill_id": "communication_break",
                        "name": "沟通断裂",
                        "description": "墨丘利释放混乱能量，导致团队沟通失效",
                        "element": "风",
                        "base_damage": 100,
                        "cooldown": 2,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "data_storm",
                        "name": "数据风暴",
                        "description": "电子数据混乱，形成破坏性的风暴",
                        "element": "风",
                        "base_damage": 80,
                        "cooldown": 1,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "reversal_fate",
                        "name": "命运逆转",
                        "description": "墨丘利的终极技能，逆转所有能量流向",
                        "element": "风",
                        "base_damage": 250,
                        "cooldown": 5,
                        "is_ultimate": True
                    }
                ]
            },
            "saturn_retrograde": {
                "name": "时间的守望者",
                "title": "土星的审判",
                "boss_type": "transit_boss",
                "trigger_event": "saturn_retrograde",
                "planet_involved": "土星",
                "zodiac_sign": None,
                "description": "土星逆行期间，时间之神的审视变得更加严厉。过去的责任、未完成的事业、业力的清算都在此时显现。",
                "lore": "土星是业力和限制的象征。逆行期间，土星让我们回顾过去，面对我们逃避的责任。这是一个艰难但必要的成长时期。",
                "base_health": 8000,
                "base_power": 200,
                "weakness_element": "水",
                "resistance_element": "土",
                "base_fluctuation": 80,
                "skills": [
                    {
                        "skill_id": "time_dilation",
                        "name": "时间膨胀",
                        "description": "土星扭曲时间流动，减缓团队行动",
                        "element": "土",
                        "base_damage": 120,
                        "cooldown": 2,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "karmic_burden",
                        "name": "业力重担",
                        "description": "土星让团队面对过去的业力，造成精神伤害",
                        "element": "土",
                        "base_damage": 150,
                        "cooldown": 3,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "final_judgment",
                        "name": "最终审判",
                        "description": "土星的终极技能，对团队进行全面审判",
                        "element": "土",
                        "base_damage": 350,
                        "cooldown": 6,
                        "is_ultimate": True
                    }
                ]
            },
            "full_moon": {
                "name": "月之女神",
                "title": "塞勒涅的狂怒",
                "boss_type": "lunar_event",
                "trigger_event": "full_moon",
                "planet_involved": "月亮",
                "zodiac_sign": None,
                "description": "满月期间，月亮的能量达到顶峰。情绪波动剧烈，直觉增强，但也可能带来情绪失控。",
                "lore": "月亮掌管情绪和潜意识。满月时，这些能量被放大。传说中，满月是灵界与物质界最接近的时刻。",
                "base_health": 6000,
                "base_power": 180,
                "weakness_element": "风",
                "resistance_element": "水",
                "base_fluctuation": 70,
                "skills": [
                    {
                        "skill_id": "lunar_tide",
                        "name": "潮汐涌动",
                        "description": "月亮引力引发情绪潮汐",
                        "element": "水",
                        "base_damage": 110,
                        "cooldown": 2,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "emotional_storm",
                        "name": "情绪风暴",
                        "description": "月亮激发深藏的情绪，造成混乱",
                        "element": "水",
                        "base_damage": 130,
                        "cooldown": 3,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "moonlit_nightmare",
                        "name": "月夜梦魇",
                        "description": "月亮的终极技能，将团队拖入最深的恐惧",
                        "element": "水",
                        "base_damage": 300,
                        "cooldown": 5,
                        "is_ultimate": True
                    }
                ]
            },
            "new_moon": {
                "name": "暗月使者",
                "title": "新月的低语",
                "boss_type": "lunar_event",
                "trigger_event": "new_moon",
                "planet_involved": "月亮",
                "zodiac_sign": None,
                "description": "新月期间，月亮隐藏在太阳的光芒中。这是新开始的时刻，但也充满了未知和不确定性。",
                "lore": "新月象征着新的开始和潜在的可能性。但在这片黑暗中，也潜伏着未知的危险。",
                "base_health": 5500,
                "base_power": 160,
                "weakness_element": "火",
                "resistance_element": "水",
                "base_fluctuation": 65,
                "skills": [
                    {
                        "skill_id": "shadow_strike",
                        "name": "暗影突袭",
                        "description": "从黑暗中发起突然攻击",
                        "element": "水",
                        "base_damage": 90,
                        "cooldown": 1,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "unknown_fear",
                        "name": "未知恐惧",
                        "description": "利用未知引发团队的恐惧",
                        "element": "水",
                        "base_damage": 140,
                        "cooldown": 3,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "void_embrace",
                        "name": "虚空拥抱",
                        "description": "新月的终极技能，将团队拖入虚空",
                        "element": "水",
                        "base_damage": 280,
                        "cooldown": 5,
                        "is_ultimate": True
                    }
                ]
            },
            "mars_square_saturn": {
                "name": "战争与约束",
                "title": "火星与土星的冲突",
                "boss_type": "aspect_boss",
                "trigger_event": "mars_square_saturn",
                "planet_involved": "火星、土星",
                "zodiac_sign": None,
                "description": "火星与土星形成四分相，行动的欲望与现实的限制发生剧烈冲突。这是一个充满挫折但也可能带来突破的时刻。",
                "lore": "火星象征行动和欲望，土星象征限制和责任。当它们形成紧张相位时，内在的冲突达到顶峰。但正是在这种张力中，真正的力量被锻造。",
                "base_health": 7500,
                "base_power": 220,
                "weakness_element": "风",
                "resistance_element": "火",
                "base_fluctuation": 85,
                "skills": [
                    {
                        "skill_id": "frustration_strike",
                        "name": "挫折打击",
                        "description": "释放被压抑的愤怒",
                        "element": "火",
                        "base_damage": 130,
                        "cooldown": 2,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "restriction_field",
                        "name": "限制领域",
                        "description": "土星的能量限制团队行动",
                        "element": "土",
                        "base_damage": 140,
                        "cooldown": 3,
                        "is_ultimate": False
                    },
                    {
                        "skill_id": "tension_eruption",
                        "name": "张力爆发",
                        "description": "火星与土星冲突的终极技能，张力达到极限后爆发",
                        "element": "火",
                        "base_damage": 400,
                        "cooldown": 6,
                        "is_ultimate": True
                    }
                ]
            }
        }
    
    def _load_or_spawn_initial_boss(self):
        """加载或生成初始BOSS"""
        try:
            current_transit_events = self._detect_current_transit_events()
            if current_transit_events:
                for event_type in current_transit_events:
                    if event_type in self.boss_templates:
                        boss = self._spawn_boss_from_template(event_type)
                        if boss:
                            self.active_bosses[boss.boss_id] = boss
                            logger.info(f"生成BOSS: {boss.name}，触发事件: {event_type}")
            
            if not self.active_bosses:
                boss = self._spawn_boss_from_template("full_moon")
                if boss:
                    self.active_bosses[boss.boss_id] = boss
                    logger.info(f"生成默认BOSS: {boss.name}")
                    
        except Exception as e:
            logger.error(f"生成初始BOSS失败: {e}")
            boss = self._create_fallback_boss()
            self.active_bosses[boss.boss_id] = boss
    
    def _detect_current_transit_events(self) -> List[str]:
        """检测当前的天象事件"""
        events = []
        now = datetime.now()
        
        try:
            jd, _ = ephemeris.local_time_to_julday(
                now.year, now.month, now.day,
                now.hour, now.minute,
                39.9042, 116.4074
            )
            
            mercury_retro = check_mercury_retrograde(jd)
            if mercury_retro.get("is_retrograde"):
                events.append("mercury_retrograde")
            
            moon_phase = calculate_moon_phase(jd)
            if moon_phase.get("is_full_moon"):
                events.append("full_moon")
            elif moon_phase.get("is_new_moon"):
                events.append("new_moon")
            
            transit_planets = ephemeris.calculate_multiple_planets(jd, MAIN_PLANETS)
            
            for planet in transit_planets:
                if planet.get("name") == "土星" and planet.get("is_retrograde"):
                    events.append("saturn_retrograde")
                    break
            
            aspects = ephemeris.calculate_all_aspects(transit_planets, transit_planets)
            for aspect in aspects:
                p1 = aspect.get("planet1_name", "")
                p2 = aspect.get("planet2_name", "")
                aspect_type = aspect.get("name", "")
                
                if ((p1 == "火星" and p2 == "土星") or (p1 == "土星" and p2 == "火星")) and aspect_type == "四分相":
                    events.append("mars_square_saturn")
                    break
                    
        except Exception as e:
            logger.error(f"检测天象事件失败: {e}")
        
        return events
    
    def _spawn_boss_from_template(self, event_type: str) -> Optional[AstroBoss]:
        """从模板生成BOSS"""
        template = self.boss_templates.get(event_type)
        if not template:
            return None
        
        boss_id = f"boss_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        skills = []
        for skill_data in template["skills"]:
            skill = BossSkill(
                skill_id=skill_data["skill_id"],
                name=skill_data["name"],
                description=skill_data["description"],
                element=skill_data["element"],
                base_damage=skill_data["base_damage"],
                cooldown=skill_data["cooldown"],
                is_ultimate=skill_data.get("is_ultimate", False)
            )
            skills.append(skill)
        
        fluctuation = template["base_fluctuation"] + random.randint(-20, 20)
        
        boss = AstroBoss(
            boss_id=boss_id,
            name=template["name"],
            title=template["title"],
            boss_type=template["boss_type"],
            trigger_event=template["trigger_event"],
            planet_involved=template["planet_involved"],
            zodiac_sign=template["zodiac_sign"],
            description=template["description"],
            lore=template["lore"],
            max_health=template["base_health"],
            current_health=template["base_health"],
            base_power=template["base_power"],
            current_power=template["base_power"],
            weakness_element=template["weakness_element"],
            resistance_element=template["resistance_element"],
            fluctuation_value=fluctuation,
            skills=skills,
            status=BossStatus.SPAWNED,
            estimated_end_at=datetime.now() + timedelta(hours=24)
        )
        
        return boss
    
    def _create_fallback_boss(self) -> AstroBoss:
        """创建备用BOSS"""
        boss_id = f"boss_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        skills = [
            BossSkill(
                skill_id="basic_attack",
                name="基础攻击",
                description="普通攻击",
                element="火",
                base_damage=50,
                cooldown=1
            )
        ]
        
        return AstroBoss(
            boss_id=boss_id,
            name="星象守护者",
            title="神秘的星灵",
            boss_type="default",
            trigger_event="system_spawn",
            planet_involved=None,
            zodiac_sign=None,
            description="一位神秘的星象守护者，守护着这片星空领域。",
            lore="传说中，每一颗星星都有一位守护者。他们在星空中默默守护，等待着勇者的挑战。",
            max_health=5000,
            current_health=5000,
            base_power=150,
            current_power=150,
            weakness_element="风",
            resistance_element="土",
            fluctuation_value=50,
            skills=skills,
            status=BossStatus.SPAWNED,
            estimated_end_at=datetime.now() + timedelta(hours=24)
        )
    
    def get_active_bosses(self) -> List[AstroBoss]:
        """获取当前活跃的BOSS"""
        self._cleanup_old_bosses()
        return list(self.active_bosses.values())
    
    def get_boss_by_id(self, boss_id: str) -> Optional[AstroBoss]:
        """根据ID获取BOSS"""
        return self.active_bosses.get(boss_id)
    
    def _cleanup_old_bosses(self):
        """清理过期的BOSS"""
        now = datetime.now()
        to_remove = []
        
        for boss_id, boss in self.active_bosses.items():
            if boss.estimated_end_at and boss.estimated_end_at < now:
                to_remove.append(boss_id)
            elif boss.status in [BossStatus.VANQUISHED, BossStatus.ESCAPED]:
                if (now - boss.spawned_at) > timedelta(hours=1):
                    to_remove.append(boss_id)
        
        for boss_id in to_remove:
            del self.active_bosses[boss_id]
            logger.info(f"清理过期BOSS: {boss_id}")
    
    def create_team(self, boss_id: str, leader_data: Dict[str, Any], team_name: str = "星之队") -> Optional[BossTeam]:
        """
        创建队伍（线程安全）
        leader_data 应该包含: member_id, name, element, combat_power, stats, passives, avatar_data
        """
        with self._lock:
            boss = self.active_bosses.get(boss_id)
            if not boss:
                logger.error(f"创建队伍失败: BOSS不存在 {boss_id}")
                return None
            
            leader_id = leader_data["member_id"]
            
            if leader_id in self._member_team_map:
                existing_team_id = self._member_team_map[leader_id]
                logger.error(f"创建队伍失败: 用户 {leader_id} 已在队伍 {existing_team_id} 中")
                return None
            
            leader = TeamMember(
                member_id=leader_id,
                name=leader_data["name"],
                element=leader_data["element"],
                combat_power=leader_data["combat_power"],
                stats=leader_data.get("stats", {}),
                passives=leader_data.get("passives", []),
                avatar_data=leader_data.get("avatar_data", {}),
                is_leader=True
            )
            
            team_id = f"team_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
            
            team = BossTeam(
                team_id=team_id,
                boss_id=boss_id,
                leader_id=leader.member_id,
                team_name=team_name
            )
            
            team.add_member(leader)
            self.active_teams[team_id] = team
            
            self._member_team_map[leader_id] = team_id
            
            logger.info(f"创建队伍成功: {team_id}，BOSS: {boss_id}，队长: {leader_id}")
            return team
    
    def get_team_by_id(self, team_id: str) -> Optional[BossTeam]:
        """根据ID获取队伍"""
        return self.active_teams.get(team_id)
    
    def get_teams_by_boss(self, boss_id: str) -> List[BossTeam]:
        """获取指定BOSS的所有队伍"""
        return [team for team in self.active_teams.values() if team.boss_id == boss_id]
    
    def add_member_to_team(self, team_id: str, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加成员到队伍（线程安全）
        member_data 应该包含: member_id, name, element, combat_power, stats, passives, avatar_data
        返回: {"success": bool, "error": str, "duplicate_member": bool, "duplicate_element": bool, "team_full": bool}
        """
        with self._lock:
            team = self.active_teams.get(team_id)
            if not team:
                logger.error(f"添加成员失败: 队伍不存在 {team_id}")
                return {"success": False, "error": "队伍不存在", "team_not_found": True}
            
            if team.status not in [TeamStatus.RECRUITING, TeamStatus.READY]:
                logger.error(f"添加成员失败: 队伍状态不允许 {team.status}")
                return {"success": False, "error": f"队伍状态不允许: {team.status}", "invalid_status": True}
            
            member_id = member_data["member_id"]
            element = member_data.get("element")
            
            if member_id in self._member_team_map:
                existing_team_id = self._member_team_map[member_id]
                if existing_team_id == team_id:
                    logger.warning(f"用户 {member_id} 已在当前队伍中")
                    return {"success": False, "error": "已在队伍中", "duplicate_member": True}
                else:
                    logger.error(f"添加成员失败: 用户 {member_id} 已在队伍 {existing_team_id} 中")
                    return {"success": False, "error": "用户已在其他队伍中", "duplicate_member": True, "other_team": existing_team_id}
            
            if len(team.members) >= 4:
                logger.error(f"添加成员失败: 队伍已满 {team_id}")
                return {"success": False, "error": "队伍已满", "team_full": True}
            
            if element in team.elements_present:
                logger.error(f"添加成员失败: 元素 {element} 已存在于队伍 {team_id} 中")
                return {"success": False, "error": f"元素 {element} 已存在于队伍中", "duplicate_element": True, "conflict_element": element}
            
            member = TeamMember(
                member_id=member_id,
                name=member_data["name"],
                element=element,
                combat_power=member_data["combat_power"],
                stats=member_data.get("stats", {}),
                passives=member_data.get("passives", []),
                avatar_data=member_data.get("avatar_data", {}),
                is_leader=False
            )
            
            success = team.add_member(member)
            if success:
                self._member_team_map[member_id] = team_id
                logger.info(f"添加成员成功: {member_id} 到队伍 {team_id}")
                return {
                    "success": True,
                    "team": self._team_to_dict(team)
                }
            else:
                return {"success": False, "error": "添加成员失败，未知错误"}
    
    def remove_member_from_team(self, team_id: str, member_id: str) -> Dict[str, Any]:
        """
        从队伍移除成员（线程安全）
        返回: {"success": bool, "error": str, "team_disbanded": bool}
        """
        with self._lock:
            team = self.active_teams.get(team_id)
            if not team:
                return {"success": False, "error": "队伍不存在"}
            
            if team.status not in [TeamStatus.RECRUITING, TeamStatus.READY]:
                return {"success": False, "error": f"队伍状态不允许: {team.status}"}
            
            member_in_team = any(m.member_id == member_id for m in team.members)
            if not member_in_team:
                return {"success": False, "error": "成员不在队伍中"}
            
            success = team.remove_member(member_id)
            if success:
                if member_id in self._member_team_map:
                    del self._member_team_map[member_id]
                logger.info(f"移除成员成功: {member_id} 从队伍 {team_id}")
                
                if len(team.members) == 0:
                    del self.active_teams[team_id]
                    logger.info(f"队伍已解散: {team_id}（无成员）")
                    return {"success": True, "team_disbanded": True}
                
                return {
                    "success": True,
                    "team": self._team_to_dict(team),
                    "team_disbanded": False
                }
            
            return {"success": False, "error": "移除成员失败"}
    
    def invite_from_encounter_atomic(self, boss_id: str, inviter_data: Dict[str, Any], 
                                      invitee_data: Dict[str, Any], team_name: str = "星之队") -> Dict[str, Any]:
        """
        从偶遇中原子化邀请组队（线程安全）
        确保要么两个成员都加入，要么都不加入，避免僵尸队伍
        """
        with self._lock:
            boss = self.active_bosses.get(boss_id)
            if not boss:
                return {"success": False, "error": "BOSS不存在"}
            
            inviter_id = inviter_data.get("member_id")
            invitee_id = invitee_data.get("member_id")
            inviter_element = inviter_data.get("element")
            invitee_element = invitee_data.get("element")
            
            logger.info(f"========================================")
            logger.info(f"🚀 开始原子组队流程")
            logger.info(f"========================================")
            logger.info(f"📦 邀请者数据:")
            logger.info(f"  - member_id: {inviter_id}")
            logger.info(f"  - name: {inviter_data.get('name')}")
            logger.info(f"  - element: {inviter_element}")
            logger.info(f"  - avatar_data: {inviter_data.get('avatar_data')}")
            logger.info(f"========================================")
            logger.info(f"📦 被邀请者数据:")
            logger.info(f"  - member_id: {invitee_id}")
            logger.info(f"  - name: {invitee_data.get('name')}")
            logger.info(f"  - element: {invitee_element}")
            logger.info(f"  - avatar_data: {invitee_data.get('avatar_data')}")
            logger.info(f"========================================")
            logger.info(f"⚠️ 元素检查:")
            logger.info(f"  - inviter_element: {inviter_element}")
            logger.info(f"  - invitee_element: {invitee_element}")
            logger.info(f"  - are_same: {inviter_element == invitee_element}")
            logger.info(f"========================================")
            
            if not inviter_id or not invitee_id:
                return {"success": False, "error": "缺少成员ID"}
            
            if inviter_element and invitee_element and inviter_element == invitee_element:
                logger.warning(f"❌ 元素相同，组队被拒绝: {inviter_element}")
                return {
                    "success": False, 
                    "error": f"邀请者和被邀请者元素相同（{inviter_element}），不能加入同一队伍",
                    "duplicate_element": True,
                    "conflict_element": inviter_element
                }
            
            if inviter_id in self._member_team_map:
                existing_team_id = self._member_team_map[inviter_id]
                return {
                    "success": False, 
                    "error": f"邀请者已在队伍 {existing_team_id} 中",
                    "duplicate_member": True,
                    "member_type": "inviter"
                }
            
            if invitee_id in self._member_team_map:
                existing_team_id = self._member_team_map[invitee_id]
                return {
                    "success": False, 
                    "error": f"被邀请者已在队伍 {existing_team_id} 中",
                    "duplicate_member": True,
                    "member_type": "invitee"
                }
            
            team_id = f"team_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
            
            inviter = TeamMember(
                member_id=inviter_id,
                name=inviter_data["name"],
                element=inviter_element,
                combat_power=inviter_data["combat_power"],
                stats=inviter_data.get("stats", {}),
                passives=inviter_data.get("passives", []),
                avatar_data=inviter_data.get("avatar_data", {}),
                is_leader=True
            )
            
            invitee = TeamMember(
                member_id=invitee_id,
                name=invitee_data["name"],
                element=invitee_element,
                combat_power=invitee_data["combat_power"],
                stats=invitee_data.get("stats", {}),
                passives=invitee_data.get("passives", []),
                avatar_data=invitee_data.get("avatar_data", {}),
                is_leader=False
            )
            
            team = BossTeam(
                team_id=team_id,
                boss_id=boss_id,
                leader_id=inviter_id,
                team_name=team_name
            )
            
            success1 = team.add_member(inviter)
            if not success1:
                logger.error(f"原子组队失败: 邀请者添加失败 {inviter_id}")
                return {"success": False, "error": "邀请者添加失败"}
            
            success2 = team.add_member(invitee)
            if not success2:
                logger.error(f"原子组队失败: 被邀请者添加失败 {invitee_id}，可能元素已存在或队伍已满")
                return {
                    "success": False, 
                    "error": "被邀请者添加失败，可能元素已存在或队伍已满",
                    "invitee_add_failed": True
                }
            
            self.active_teams[team_id] = team
            self._member_team_map[inviter_id] = team_id
            self._member_team_map[invitee_id] = team_id
            
            logger.info(f"✅ 原子组队成功: 队伍 {team_id}")
            logger.info(f"   - 邀请者 {inviter_id} ({inviter.name}) - 元素: {inviter.element}")
            logger.info(f"   - 被邀请者 {invitee_id} ({invitee.name}) - 元素: {invitee.element}")
            logger.info(f"========================================")
            
            return {
                "success": True,
                "team": self._team_to_dict(team),
                "members_added": 2
            }
    
    def get_member_current_team(self, member_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户当前所在的队伍
        """
        with self._lock:
            team_id = self._member_team_map.get(member_id)
            if not team_id:
                return None
            
            team = self.active_teams.get(team_id)
            if team:
                return self._team_to_dict(team)
            return None
    
    def leave_team(self, member_id: str) -> Dict[str, Any]:
        """
        用户离开当前队伍（线程安全）
        """
        with self._lock:
            team_id = self._member_team_map.get(member_id)
            if not team_id:
                return {"success": False, "error": "用户不在任何队伍中"}
            
            return self.remove_member_from_team(team_id, member_id)
    
    async def start_battle_async(self, team_id: str) -> Dict[str, Any]:
        """
        开始战斗（异步非阻塞）
        - 先返回战斗ID，后台异步生成AI史诗剧情
        """
        with self._lock:
            team = self.active_teams.get(team_id)
            if not team:
                return {
                    "success": False,
                    "error": "队伍不存在"
                }
            
            if not team.has_all_elements():
                missing = team.get_missing_elements()
                return {
                    "success": False,
                    "error": f"队伍元素不完整，缺少: {', '.join(missing)}",
                    "missing_elements": missing,
                    "has_all_elements": False
                }
            
            if team.status != TeamStatus.READY:
                return {
                    "success": False,
                    "error": f"队伍状态不正确: {team.status}，需要状态为 ready",
                    "current_status": team.status
                }
            
            boss = self.active_bosses.get(team.boss_id)
            if not boss:
                return {
                    "success": False,
                    "error": "BOSS不存在"
                }
            
            battle_id = f"battle_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
            
            team.status = TeamStatus.FIGHTING
            boss.status = BossStatus.FIGHTING
            team.battle_started_at = datetime.now()
            
            self._pending_battles[battle_id] = {
                "team_id": team_id,
                "boss_id": boss.boss_id,
                "status": "processing",
                "created_at": datetime.now()
            }
            
            logger.info(f"战斗已启动（异步）: battle_id={battle_id}, 队伍 {team_id} vs BOSS {boss.boss_id}")
            
            return {
                "success": True,
                "battle_id": battle_id,
                "team_id": team_id,
                "boss_id": boss.boss_id,
                "status": "processing",
                "message": "战斗已开始，正在生成史诗剧情...",
                "team": self._team_to_dict(team)
            }
    
    async def _execute_battle_async(self, battle_id: str, team: BossTeam, boss: AstroBoss):
        """
        后台异步执行战斗
        """
        try:
            logger.info(f"开始异步战斗执行: {battle_id}")
            
            battle_story = await self._generate_battle_story(team, boss)
            
            battle_result = self._calculate_battle_outcome(team, boss)
            
            if battle_result.get("victory"):
                team.status = TeamStatus.VICTORIOUS
                boss.status = BossStatus.VANQUISHED
                rewards = self._calculate_rewards(team, boss, battle_result)
                team.rewards_earned = rewards
            else:
                team.status = TeamStatus.DEFEATED
            
            team.battle_ended_at = datetime.now()
            boss.participant_count += len(team.members)
            
            result = {
                "success": True,
                "team_id": team.team_id,
                "boss_id": boss.boss_id,
                "battle_story": battle_story,
                "battle_result": battle_result,
                "team": self._team_to_dict(team),
                "boss": self._boss_to_dict(boss),
                "completed_at": datetime.now().isoformat()
            }
            
            self._battle_results[battle_id] = result
            
            if battle_id in self._pending_battles:
                del self._pending_battles[battle_id]
            
            logger.info(f"异步战斗完成: {battle_id}, 胜利={battle_result.get('victory')}")
            
        except Exception as e:
            logger.error(f"异步战斗执行失败: {battle_id}, 错误: {e}")
            self._battle_results[battle_id] = {
                "success": False,
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            }
            if battle_id in self._pending_battles:
                del self._pending_battles[battle_id]
    
    def get_battle_result(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """
        获取战斗结果
        """
        with self._lock:
            if battle_id in self._battle_results:
                return self._battle_results[battle_id]
            
            if battle_id in self._pending_battles:
                return {
                    "success": True,
                    "status": "processing",
                    "message": "战斗正在进行中，正在生成史诗剧情..."
                }
            
            return None
    
    def trigger_battle_background(self, battle_id: str):
        """
        触发后台战斗执行（用于FastAPI后台任务）
        """
        with self._lock:
            pending = self._pending_battles.get(battle_id)
            if not pending:
                return
            
            team = self.active_teams.get(pending["team_id"])
            boss = self.active_bosses.get(pending["boss_id"])
            
            if not team or not boss:
                return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._execute_battle_async(battle_id, team, boss))
            loop.close()
        except Exception as e:
            logger.error(f"后台战斗执行异常: {e}")
    
    async def start_battle(self, team_id: str) -> Dict[str, Any]:
        """
        开始战斗
        1. 验证队伍状态
        2. 生成战斗剧情
        3. 计算战斗结果
        4. 发放奖励
        """
        team = self.active_teams.get(team_id)
        if not team:
            return {
                "success": False,
                "error": "队伍不存在"
            }
        
        if team.status != TeamStatus.READY:
            return {
                "success": False,
                "error": f"队伍状态不正确: {team.status}，需要状态为 ready"
            }
        
        boss = self.active_bosses.get(team.boss_id)
        if not boss:
            return {
                "success": False,
                "error": "BOSS不存在"
            }
        
        team.status = TeamStatus.FIGHTING
        boss.status = BossStatus.FIGHTING
        team.battle_started_at = datetime.now()
        
        logger.info(f"开始战斗: 队伍 {team_id} vs BOSS {boss.boss_id}")
        
        battle_story = await self._generate_battle_story(team, boss)
        
        battle_result = self._calculate_battle_outcome(team, boss)
        
        if battle_result.get("victory"):
            team.status = TeamStatus.VICTORIOUS
            boss.status = BossStatus.VANQUISHED
            rewards = self._calculate_rewards(team, boss, battle_result)
            team.rewards_earned = rewards
        else:
            team.status = TeamStatus.DEFEATED
        
        team.battle_ended_at = datetime.now()
        boss.participant_count += len(team.members)
        
        return {
            "success": True,
            "team_id": team_id,
            "boss_id": boss.boss_id,
            "battle_story": battle_story,
            "battle_result": battle_result,
            "team": self._team_to_dict(team),
            "boss": self._boss_to_dict(boss)
        }
    
    async def _generate_battle_story(self, team: BossTeam, boss: AstroBoss) -> Dict[str, Any]:
        """调用DeepSeek生成史诗级战斗剧情"""
        try:
            members_info = []
            for i, member in enumerate(team.members):
                member_info = f"""
角色{i+1}: {member.name}
- 元素: {ELEMENT_SYMBOLS.get(member.element, '❓')} {member.element}
- 战力: {member.combat_power}
- 被动技能: {', '.join([p.get('name', '') for p in member.passives]) if member.passives else '无'}
"""
                members_info.append(member_info)
            
            members_str = "\n".join(members_info)
            
            skills_info = []
            for skill in boss.skills:
                skill_info = f"- {skill.name}: {skill.description} (伤害: {skill.base_damage}, 元素: {skill.element})"
                skills_info.append(skill_info)
            skills_str = "\n".join(skills_info)
            
            system_prompt = """你是一位史诗级奇幻故事作家，擅长创作宏大的RPG战斗场景。请根据以下信息，生成一段史诗级的星盘RPG战斗剧情。

要求：
1. 战斗剧情要宏大、紧张、有画面感
2. 每个队员都要有高光时刻
3. 要体现元素相克（弱点元素造成额外伤害，抵抗元素造成较少伤害）
4. 要包含BOSS的技能释放
5. 要有紧张的战斗节奏和情感张力
6. 结尾要暗示战斗结果但不要明确宣告胜负

输出格式（JSON）：
{
    "scene_intro": "战斗开场场景描述",
    "battle_phases": [
        {
            "phase_name": "第一阶段：遭遇",
            "description": "阶段描述",
            "key_actions": ["动作1", "动作2"]
        }
    ],
    "climax": "高潮场景",
    "character_highlights": [
        {"character": "角色名", "highlight": "高光时刻描述"}
    ],
    "epic_quotes": ["史诗台词1", "史诗台词2"]
}

请严格输出JSON格式，不要添加额外的解释。"""
            
            user_prompt = f"""【BOSS信息】
名称: {boss.name}
称号: {boss.title}
类型: {boss.boss_type}
触发天象: {boss.trigger_event}
涉及行星: {boss.planet_involved or '无'}
生命值: {boss.max_health}
攻击力: {boss.current_power}
弱点元素: {ELEMENT_SYMBOLS.get(boss.weakness_element, '❓')} {boss.weakness_element}
抵抗元素: {ELEMENT_SYMBOLS.get(boss.resistance_element, '❓')} {boss.resistance_element}
星象波动值: {boss.fluctuation_value}

BOSS背景故事: {boss.lore}

BOSS技能:
{skills_str}

【队伍信息】
队伍名称: {team.team_name}
队伍总能量: {team.total_energy}
队伍元素覆盖: {', '.join([ELEMENT_SYMBOLS.get(e, '❓') + e for e in team.elements_present])}

队伍成员:
{members_str}

【战斗背景】
这是一场基于星象的史诗战斗。{boss.name}因{boss.trigger_event}天象事件而现身。
队伍必须利用各自的星盘能量，特别是{boss.weakness_element}元素来击败这个强大的星象BOSS。

请生成一段史诗级的战斗剧情！"""
            
            story_text = await call_deepseek_api(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.85,
                max_tokens=4000,
                fast_mode=True
            )
            
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', story_text)
                if json_match:
                    story_json = json.loads(json_match.group())
                    return story_json
                else:
                    return {
                        "scene_intro": story_text[:500] if story_text else "战斗开始...",
                        "battle_phases": [],
                        "climax": "",
                        "character_highlights": [],
                        "epic_quotes": []
                    }
            except json.JSONDecodeError:
                return {
                    "scene_intro": story_text[:500] if story_text else "战斗开始...",
                    "raw_text": story_text
                }
                
        except Exception as e:
            logger.error(f"生成战斗剧情失败: {e}")
            return {
                "scene_intro": f"{team.team_name} 与 {boss.name} 的战斗开始了！",
                "error": str(e)
            }
    
    def _calculate_battle_outcome(self, team: BossTeam, boss: AstroBoss) -> Dict[str, Any]:
        """
        计算战斗结果
        基于:
        1. 队伍总能量 vs BOSS波动值
        2. 元素克制加成
        3. 随机因素
        """
        base_team_power = team.total_energy
        
        element_bonus = 0
        for member in team.members:
            if member.element == boss.weakness_element:
                element_bonus += int(member.combat_power * 0.3)
            elif member.element == boss.resistance_element:
                element_bonus -= int(member.combat_power * 0.15)
        
        adjusted_team_power = base_team_power + element_bonus
        
        boss_power = boss.fluctuation_value * 10
        
        power_ratio = adjusted_team_power / boss_power if boss_power > 0 else 1.0
        
        random_factor = random.uniform(0.85, 1.15)
        
        final_ratio = power_ratio * random_factor
        
        victory = final_ratio >= 0.7
        
        if victory:
            victory_chance = min(95, max(50, final_ratio * 100))
            victory = random.random() * 100 < victory_chance
        
        damage_dealt = int(adjusted_team_power * random.uniform(0.8, 1.2))
        damage_received = int(boss.current_power * random.uniform(0.5, 1.0))
        
        boss.current_health = max(0, boss.current_health - damage_dealt)
        boss.total_damage_received += damage_dealt
        team.damage_contributed += damage_dealt
        
        return {
            "victory": victory,
            "team_power": base_team_power,
            "adjusted_team_power": adjusted_team_power,
            "boss_power": boss_power,
            "power_ratio": round(power_ratio, 2),
            "element_bonus": element_bonus,
            "damage_dealt": damage_dealt,
            "damage_received": damage_received,
            "boss_remaining_health": boss.current_health,
            "random_factor": round(random_factor, 2)
        }
    
    def _calculate_rewards(self, team: BossTeam, boss: AstroBoss, battle_result: Dict[str, Any]) -> Dict[str, Any]:
        """计算奖励"""
        base_stardust = 100
        
        difficulty_multiplier = {
            50: 1.0,
            60: 1.2,
            70: 1.5,
            80: 2.0,
            85: 2.5
        }
        
        multiplier = 1.0
        for threshold, mult in sorted(difficulty_multiplier.items()):
            if boss.fluctuation_value >= threshold:
                multiplier = mult
        
        performance_bonus = 1.0
        if battle_result.get("power_ratio", 0) >= 1.5:
            performance_bonus = 1.3
        elif battle_result.get("power_ratio", 0) >= 1.0:
            performance_bonus = 1.1
        
        element_bonus = 1.0
        if boss.weakness_element in team.elements_present:
            element_bonus = 1.2
        
        total_stardust = int(base_stardust * multiplier * performance_bonus * element_bonus)
        
        per_member_stardust = total_stardust // max(1, len(team.members))
        
        rewards = {
            "total_stardust": total_stardust,
            "per_member_stardust": per_member_stardust,
            "multipliers": {
                "difficulty": multiplier,
                "performance": performance_bonus,
                "element": element_bonus
            },
            "items": []
        }
        
        drop_chance = battle_result.get("power_ratio", 0.5)
        if random.random() < drop_chance * 0.3:
            rewards["items"].append({
                "item_id": "boss_essence",
                "item_name": f"{boss.name}的精华",
                "rarity": "rare" if boss.fluctuation_value >= 70 else "uncommon",
                "description": f"击败{boss.name}后获得的珍贵精华"
            })
        
        return rewards
    
    def _team_to_dict(self, team: BossTeam) -> Dict[str, Any]:
        """将队伍转换为字典"""
        return {
            "team_id": team.team_id,
            "boss_id": team.boss_id,
            "leader_id": team.leader_id,
            "team_name": team.team_name,
            "status": team.status.value if hasattr(team.status, 'value') else team.status,
            "members": [
                {
                    "member_id": m.member_id,
                    "name": m.name,
                    "element": m.element,
                    "element_symbol": ELEMENT_SYMBOLS.get(m.element, "❓"),
                    "combat_power": m.combat_power,
                    "is_leader": m.is_leader
                }
                for m in team.members
            ],
            "elements_present": team.elements_present,
            "missing_elements": team.get_missing_elements(),
            "has_all_elements": team.has_all_elements(),
            "total_energy": team.total_energy,
            "damage_contributed": team.damage_contributed,
            "rewards_earned": team.rewards_earned,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "battle_started_at": team.battle_started_at.isoformat() if team.battle_started_at else None,
            "battle_ended_at": team.battle_ended_at.isoformat() if team.battle_ended_at else None
        }
    
    def _boss_to_dict(self, boss: AstroBoss) -> Dict[str, Any]:
        """将BOSS转换为字典"""
        return {
            "boss_id": boss.boss_id,
            "name": boss.name,
            "title": boss.title,
            "boss_type": boss.boss_type,
            "trigger_event": boss.trigger_event,
            "planet_involved": boss.planet_involved,
            "zodiac_sign": boss.zodiac_sign,
            "description": boss.description,
            "lore": boss.lore,
            "max_health": boss.max_health,
            "current_health": boss.current_health,
            "health_percentage": round((boss.current_health / boss.max_health) * 100, 1) if boss.max_health > 0 else 0,
            "base_power": boss.base_power,
            "current_power": boss.current_power,
            "weakness_element": boss.weakness_element,
            "weakness_symbol": ELEMENT_SYMBOLS.get(boss.weakness_element, "❓"),
            "resistance_element": boss.resistance_element,
            "resistance_symbol": ELEMENT_SYMBOLS.get(boss.resistance_element, "❓"),
            "fluctuation_value": boss.fluctuation_value,
            "skills": [
                {
                    "skill_id": s.skill_id,
                    "name": s.name,
                    "description": s.description,
                    "element": s.element,
                    "element_symbol": ELEMENT_SYMBOLS.get(s.element, "❓"),
                    "base_damage": s.base_damage,
                    "cooldown": s.cooldown,
                    "is_ultimate": s.is_ultimate
                }
                for s in boss.skills
            ],
            "status": boss.status.value if hasattr(boss.status, 'value') else boss.status,
            "spawned_at": boss.spawned_at.isoformat() if boss.spawned_at else None,
            "estimated_end_at": boss.estimated_end_at.isoformat() if boss.estimated_end_at else None,
            "total_damage_received": boss.total_damage_received,
            "participant_count": boss.participant_count
        }


boss_battle_service = BossBattleService()


def get_boss_battle_service() -> BossBattleService:
    """获取BOSS战斗服务单例"""
    return boss_battle_service
