"""子网计算工具 API"""
from fastapi import APIRouter, HTTPException, Query

from app.tools.subnet import SubnetCalculator

router = APIRouter()


@router.get("/subnet", summary="子网信息计算")
def calc_subnet(
    ip: str = Query(..., description="IP 地址，如 192.168.1.10"),
    mask: str = Query(
        ...,
        description="子网掩码或前缀长度，如 255.255.255.0 或 24",
    ),
) -> dict:
    """根据 IP + 掩码（或前缀）计算网络地址、广播地址、可用主机范围等子网信息。"""
    result = SubnetCalculator.calculate(ip, mask)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error") or "计算失败")
    return result


@router.get("/subnet/split", summary="子网划分")
def split_subnet(
    network: str = Query(..., description="原网络地址"),
    prefix: int = Query(..., ge=0, le=32, description="原前缀长度"),
    new_prefix: int = Query(..., ge=0, le=32, description="新前缀长度"),
) -> dict:
    """把一个网段按新前缀长度切分为若干等长子网。"""
    if new_prefix <= prefix:
        raise HTTPException(status_code=400, detail="新前缀必须大于原前缀")
    subnets = SubnetCalculator.split_subnet(network, prefix, new_prefix)
    if not subnets:
        raise HTTPException(status_code=400, detail="划分失败，请检查输入参数")
    return {"count": len(subnets), "subnets": subnets}


@router.get("/subnet/range-to-cidr", summary="IP 范围转 CIDR")
def ip_range_to_cidr(
    start: str = Query(..., description="起始 IP"),
    end: str = Query(..., description="结束 IP"),
) -> dict:
    """给定 IP 范围，输出最少的 CIDR 块表示。"""
    cidrs = SubnetCalculator.ip_range_to_cidr(start, end)
    if not cidrs:
        raise HTTPException(status_code=400, detail="转换失败，请检查 IP 范围")
    return {"count": len(cidrs), "cidrs": cidrs}
