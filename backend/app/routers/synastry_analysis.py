from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
import secrets
import logging

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, SynastryRecord
from app.routers.users import get_current_user
from app.schemas import ApiResponse, SynastryCalculateRequest
from app.synastry import calculate_synastry_chart
from app.synastry_analysis import generate_full_analysis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合盘深度分析"])


class SaveSynastryRequest(BaseModel):
    name: Optional[str] = None
    person_a_name: Optional[str] = None
    person_a_birth_date: str
    person_a_birth_time: str
    person_a_birth_place: Optional[str] = None
    person_a_latitude: float
    person_a_longitude: float
    person_b_name: Optional[str] = None
    person_b_birth_date: str
    person_b_birth_time: str
    person_b_birth_place: Optional[str] = None
    person_b_latitude: float
    person_b_longitude: float
    synastry_data: Dict[str, Any]
    analysis_data: Optional[Dict[str, Any]] = None


class UpdateSynastryRequest(BaseModel):
    name: Optional[str] = None
    is_public: Optional[bool] = None


def generate_share_code() -> str:
    return secrets.token_urlsafe(12)[:15]


@router.post("/calculate-and-analyze", response_model=ApiResponse)
def calculate_and_analyze(
    request: SynastryCalculateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    try:
        person_a = {
            "name": request.person_a.name or "人物A",
            "birth_date": request.person_a.birth_date,
            "birth_time": request.person_a.birth_time,
            "birth_place": request.person_a.birth_place or "",
            "latitude": request.person_a.latitude,
            "longitude": request.person_a.longitude,
            "house_system": request.person_a.house_system or "placidus"
        }
        
        person_b = {
            "name": request.person_b.name or "人物B",
            "birth_date": request.person_b.birth_date,
            "birth_time": request.person_b.birth_time,
            "birth_place": request.person_b.birth_place or "",
            "latitude": request.person_b.latitude,
            "longitude": request.person_b.longitude,
            "house_system": request.person_b.house_system or "placidus"
        }
        
        synastry_data = calculate_synastry_chart(person_a, person_b)
        
        analysis_data = generate_full_analysis(synastry_data)
        
        logger.info(f"合盘深度分析完成: {person_a['name']} & {person_b['name']}, 总分: {analysis_data.get('compatibility', {}).get('total_score', 0)}")
        
        result = {
            "synastry": synastry_data,
            "analysis": analysis_data
        }
        
        return ApiResponse(
            message="合盘深度分析完成",
            data=result
        )
        
    except Exception as e:
        logger.error(f"合盘深度分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合盘深度分析失败: {str(e)}"
        )


@router.post("/save", response_model=ApiResponse)
def save_synastry_record(
    request: SaveSynastryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        share_code = generate_share_code()
        
        total_score = None
        if request.analysis_data:
            total_score = request.analysis_data.get('compatibility', {}).get('total_score')
        
        record = SynastryRecord(
            user_id=current_user.id,
            name=request.name or f"{request.person_a_name or '人物A'} & {request.person_b_name or '人物B'}",
            person_a_name=request.person_a_name,
            person_a_birth_date=request.person_a_birth_date,
            person_a_birth_time=request.person_a_birth_time,
            person_a_birth_place=request.person_a_birth_place,
            person_a_latitude=request.person_a_latitude,
            person_a_longitude=request.person_a_longitude,
            person_b_name=request.person_b_name,
            person_b_birth_date=request.person_b_birth_date,
            person_b_birth_time=request.person_b_birth_time,
            person_b_birth_place=request.person_b_birth_place,
            person_b_latitude=request.person_b_latitude,
            person_b_longitude=request.person_b_longitude,
            synastry_data=json.dumps(request.synastry_data, ensure_ascii=False),
            analysis_data=json.dumps(request.analysis_data, ensure_ascii=False) if request.analysis_data else None,
            share_code=share_code,
            total_score=total_score
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return ApiResponse(
            message="合盘记录保存成功",
            data={
                "id": record.id,
                "share_code": record.share_code,
                "name": record.name,
                "total_score": record.total_score
            }
        )
        
    except Exception as e:
        logger.error(f"保存合盘记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存合盘记录失败: {str(e)}"
        )


@router.get("/list", response_model=ApiResponse)
def get_synastry_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        query = db.query(SynastryRecord).filter(
            SynastryRecord.user_id == current_user.id,
            SynastryRecord.is_deleted == False
        )
        
        total = query.count()
        
        records = query.order_by(
            SynastryRecord.created_at.desc()
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        result = []
        for record in records:
            analysis_data = None
            if record.analysis_data:
                try:
                    analysis_data = json.loads(record.analysis_data)
                except:
                    pass
            
            result.append({
                "id": record.id,
                "name": record.name,
                "person_a_name": record.person_a_name,
                "person_a_birth_date": record.person_a_birth_date,
                "person_b_name": record.person_b_name,
                "person_b_birth_date": record.person_b_birth_date,
                "total_score": record.total_score,
                "share_code": record.share_code,
                "is_public": record.is_public,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "score_level": analysis_data.get('compatibility', {}).get('score_level', {}) if analysis_data else {}
            })
        
        return ApiResponse(
            message="获取合盘记录列表成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "records": result
            }
        )
        
    except Exception as e:
        logger.error(f"获取合盘记录列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取合盘记录列表失败: {str(e)}"
        )


@router.get("/{record_id}", response_model=ApiResponse)
def get_synastry_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        record = db.query(SynastryRecord).filter(
            SynastryRecord.id == record_id,
            SynastryRecord.is_deleted == False
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合盘记录不存在"
            )
        
        if record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此合盘记录"
            )
        
        synastry_data = None
        if record.synastry_data:
            try:
                synastry_data = json.loads(record.synastry_data)
            except:
                pass
        
        analysis_data = None
        if record.analysis_data:
            try:
                analysis_data = json.loads(record.analysis_data)
            except:
                pass
        
        return ApiResponse(
            message="获取合盘记录详情成功",
            data={
                "id": record.id,
                "name": record.name,
                "person_a_name": record.person_a_name,
                "person_a_birth_date": record.person_a_birth_date,
                "person_a_birth_time": record.person_a_birth_time,
                "person_a_birth_place": record.person_a_birth_place,
                "person_a_latitude": record.person_a_latitude,
                "person_a_longitude": record.person_a_longitude,
                "person_b_name": record.person_b_name,
                "person_b_birth_date": record.person_b_birth_date,
                "person_b_birth_time": record.person_b_birth_time,
                "person_b_birth_place": record.person_b_birth_place,
                "person_b_latitude": record.person_b_latitude,
                "person_b_longitude": record.person_b_longitude,
                "synastry_data": synastry_data,
                "analysis_data": analysis_data,
                "share_code": record.share_code,
                "total_score": record.total_score,
                "is_public": record.is_public,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取合盘记录详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取合盘记录详情失败: {str(e)}"
        )


@router.put("/{record_id}", response_model=ApiResponse)
def update_synastry_record(
    record_id: int,
    request: UpdateSynastryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        record = db.query(SynastryRecord).filter(
            SynastryRecord.id == record_id,
            SynastryRecord.is_deleted == False
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合盘记录不存在"
            )
        
        if record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此合盘记录"
            )
        
        if request.name is not None:
            record.name = request.name
        if request.is_public is not None:
            record.is_public = request.is_public
        
        db.commit()
        
        return ApiResponse(
            message="更新合盘记录成功",
            data={
                "id": record.id,
                "name": record.name,
                "is_public": record.is_public
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新合盘记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新合盘记录失败: {str(e)}"
        )


@router.delete("/{record_id}", response_model=ApiResponse)
def delete_synastry_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        record = db.query(SynastryRecord).filter(
            SynastryRecord.id == record_id,
            SynastryRecord.is_deleted == False
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合盘记录不存在"
            )
        
        if record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此合盘记录"
            )
        
        record.is_deleted = True
        db.commit()
        
        return ApiResponse(
            message="删除合盘记录成功",
            data={"id": record_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除合盘记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除合盘记录失败: {str(e)}"
        )


@router.post("/{record_id}/generate-share", response_model=ApiResponse)
def generate_share_link(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        record = db.query(SynastryRecord).filter(
            SynastryRecord.id == record_id,
            SynastryRecord.is_deleted == False
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合盘记录不存在"
            )
        
        if record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此合盘记录"
            )
        
        if not record.share_code:
            record.share_code = generate_share_code()
            db.commit()
        
        return ApiResponse(
            message="生成分享链接成功",
            data={
                "share_code": record.share_code,
                "share_url": f"/synastry/share/{record.share_code}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成分享链接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成分享链接失败: {str(e)}"
        )


@router.get("/share/{share_code}", response_model=ApiResponse)
def get_shared_synastry(
    share_code: str,
    db: Session = Depends(get_db)
):
    try:
        record = db.query(SynastryRecord).filter(
            SynastryRecord.share_code == share_code,
            SynastryRecord.is_deleted == False
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享链接无效或已过期"
            )
        
        if not record.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此合盘记录未公开"
            )
        
        analysis_data = None
        if record.analysis_data:
            try:
                analysis_data = json.loads(record.analysis_data)
            except:
                pass
        
        return ApiResponse(
            message="获取分享合盘成功",
            data={
                "name": record.name,
                "person_a_name": record.person_a_name,
                "person_a_birth_date": record.person_a_birth_date,
                "person_b_name": record.person_b_name,
                "person_b_birth_date": record.person_b_birth_date,
                "analysis_data": analysis_data,
                "total_score": record.total_score,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分享合盘失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享合盘失败: {str(e)}"
        )
