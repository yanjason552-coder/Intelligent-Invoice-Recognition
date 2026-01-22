import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func

from app.api.deps import (
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    CompanyPublic,
    CompaniesPublic,
    User,
    Message,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=CompaniesPublic,
)
def read_companies(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取公司列表
    """
    count_statement = select(func.count()).select_from(Company)
    count = session.exec(count_statement).one()

    statement = select(Company).offset(skip).limit(limit)
    companies = session.exec(statement).all()

    # 计算每个公司的用户数量
    result = []
    for company in companies:
        user_count = session.exec(
            select(func.count()).select_from(User).where(User.company_id == company.id)
        ).one()
        company_public = CompanyPublic(
            **company.model_dump(),
            user_count=user_count
        )
        result.append(company_public)

    return CompaniesPublic(data=result, count=count)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=CompanyPublic,
)
def create_company(
    *,
    session: SessionDep,
    company_in: CompanyCreate,
) -> Any:
    """
    创建新公司
    """
    # 检查公司代码是否已存在
    existing_company = session.exec(
        select(Company).where(Company.code == company_in.code)
    ).first()
    if existing_company:
        raise HTTPException(
            status_code=400,
            detail="该公司代码已存在",
        )

    company = Company(**company_in.model_dump())
    session.add(company)
    session.commit()
    session.refresh(company)
    
    # 计算用户数量
    user_count = session.exec(
        select(func.count()).select_from(User).where(User.company_id == company.id)
    ).one()
    
    return CompanyPublic(**company.model_dump(), user_count=user_count)


@router.get(
    "/{company_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=CompanyPublic,
)
def read_company(
    company_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    根据ID获取公司
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    
    # 计算用户数量
    user_count = session.exec(
        select(func.count()).select_from(User).where(User.company_id == company_id)
    ).one()
    
    return CompanyPublic(**company.model_dump(), user_count=user_count)


@router.patch(
    "/{company_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=CompanyPublic,
)
def update_company(
    *,
    session: SessionDep,
    company_id: uuid.UUID,
    company_in: CompanyUpdate,
) -> Any:
    """
    更新公司
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    # 如果更新代码，检查是否冲突
    if company_in.code and company_in.code != company.code:
        existing_company = session.exec(
            select(Company).where(Company.code == company_in.code)
        ).first()
        if existing_company:
            raise HTTPException(
                status_code=400,
                detail="该公司代码已存在",
            )

    company_data = company_in.model_dump(exclude_unset=True)
    company.sqlmodel_update(company_data)
    session.add(company)
    session.commit()
    session.refresh(company)
    
    # 计算用户数量
    user_count = session.exec(
        select(func.count()).select_from(User).where(User.company_id == company_id)
    ).one()
    
    return CompanyPublic(**company.model_dump(), user_count=user_count)


@router.delete(
    "/{company_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_company(
    *,
    session: SessionDep,
    company_id: uuid.UUID,
) -> Any:
    """
    删除公司
    """
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    # 检查是否有用户关联
    user_count = session.exec(
        select(func.count()).select_from(User).where(User.company_id == company_id)
    ).one()
    
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除公司，仍有 {user_count} 个用户关联",
        )

    session.delete(company)
    session.commit()
    return Message(message="公司删除成功")

