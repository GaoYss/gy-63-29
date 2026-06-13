from fastapi import APIRouter

from app.modules.members.models import DuplicatePhoneItem, Member, MemberCreate, MemberMergeRequest, MemberMergeResult, MemberUpdate
from app.modules.members.service import create_member, find_duplicate_phones, list_members, merge_members, update_member

router = APIRouter()


@router.get("", response_model=list[Member])
def get_members() -> list[Member]:
    return list_members()


@router.get("/duplicates", response_model=list[DuplicatePhoneItem])
def get_duplicate_members() -> list[DuplicatePhoneItem]:
    return find_duplicate_phones()


@router.post("", response_model=Member, status_code=201)
def post_member(payload: MemberCreate) -> Member:
    return create_member(payload)


@router.post("/merge", response_model=MemberMergeResult)
def post_merge_members(payload: MemberMergeRequest) -> MemberMergeResult:
    return merge_members(payload.source_member_id, payload.target_member_id)


@router.patch("/{member_id}", response_model=Member)
def patch_member(member_id: int, payload: MemberUpdate) -> Member:
    return update_member(member_id, payload)
