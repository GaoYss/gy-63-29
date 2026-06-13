from fastapi import HTTPException

from app.core.store import store
from app.modules.levels.service import get_level
from app.modules.members.models import DuplicatePhoneItem, Member, MemberCreate, MemberMergeResult, MemberUpdate


def _with_level(member: dict) -> Member:
    level = get_level(member["level_id"])
    return Member(**member, level=level)


def list_members() -> list[Member]:
    return [_with_level(member) for member in store.members.values()]


def get_member(member_id: int) -> Member:
    member = store.members.get(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    return _with_level(member)


def create_member(payload: MemberCreate) -> Member:
    get_level(payload.level_id)
    member_id = store.next_id(store.members)
    member = {"id": member_id, **payload.model_dump()}
    store.members[member_id] = member
    return _with_level(member)


def update_member(member_id: int, payload: MemberUpdate) -> Member:
    existing = store.members.get(member_id)
    if not existing:
        raise HTTPException(status_code=404, detail="会员不存在")

    updates = payload.model_dump(exclude_unset=True)
    if "level_id" in updates:
        get_level(updates["level_id"])
    existing.update(updates)
    return _with_level(existing)


def find_duplicate_phones() -> list[DuplicatePhoneItem]:
    phone_groups: dict[str, list[dict]] = {}
    for member in store.members.values():
        phone = member["phone"]
        if phone not in phone_groups:
            phone_groups[phone] = []
        phone_groups[phone].append(member)

    result = []
    for phone, members in phone_groups.items():
        if len(members) > 1:
            result.append(
                DuplicatePhoneItem(
                    phone=phone,
                    members=[_with_level(member) for member in members],
                )
            )
    return result


def merge_members(source_member_id: int, target_member_id: int) -> MemberMergeResult:
    if source_member_id == target_member_id:
        raise HTTPException(status_code=400, detail="源会员和目标会员不能相同")

    source_member = store.members.get(source_member_id)
    target_member = store.members.get(target_member_id)

    if not source_member:
        raise HTTPException(status_code=404, detail="源会员不存在")
    if not target_member:
        raise HTTPException(status_code=404, detail="目标会员不存在")
    if source_member["phone"] != target_member["phone"]:
        raise HTTPException(status_code=400, detail="两个会员手机号不相同，无法合并")

    merged_points = source_member["points"]
    target_member["points"] += source_member["points"]

    merged_records_count = 0
    for record in store.point_records:
        if record["member_id"] == source_member_id:
            record["member_id"] = target_member_id
            merged_records_count += 1

    merged_orders_count = 0
    for order in store.presale_orders:
        if order["member_id"] == source_member_id:
            order["member_id"] = target_member_id
            merged_orders_count += 1

    source_categories = set(source_member["favorite_categories"])
    target_categories = set(target_member["favorite_categories"])
    merged_categories = sorted(source_categories | target_categories)
    target_member["favorite_categories"] = merged_categories

    target_level = get_level(target_member["level_id"])
    source_level = get_level(source_member["level_id"])
    if source_level.min_points > target_level.min_points:
        target_member["level_id"] = source_member["level_id"]

    del store.members[source_member_id]

    return MemberMergeResult(
        target_member=_with_level(target_member),
        merged_points=merged_points,
        merged_records_count=merged_records_count,
        merged_orders_count=merged_orders_count,
    )
