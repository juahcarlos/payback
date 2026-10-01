import random
import re
import string
from datetime import UTC, datetime, timedelta

from fastapi import Depends

from app.domain.coupons import CouponCheckModel, CouponReadModel, CouponSaveModel
from app.repositories import CouponDBRepo, get_coupon_repo
from app.utils.datetime import utc_now_naive


class CouponService:
    def __init__(self, repo: CouponDBRepo):
        self.repo = repo

    @staticmethod
    def generate_coupon_code() -> str:
        random_part = "".join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(10)]  # noqa: S311
        ).upper()
        return f"COUPON{random_part}"

    def get_coupon_data(self) -> CouponSaveModel:
        return CouponSaveModel(
            coupon=self.generate_coupon_code(),
            percent=10,
            created=utc_now_naive(),
            expiration=utc_now_naive() + timedelta(days=30),
        )

    async def create_new_coupon(self) -> CouponSaveModel:
        coupon_data = self.get_coupon_data()
        await self.repo.insert_coupon(coupon_data)
        return coupon_data

    async def get_coupon_by_code(self, coupon_code: str) -> CouponReadModel | None:
        return await self.repo.get_coupon_by_code(coupon_code)

    async def generate_new_coupon(
            self,
            discount: int,
            days_valid: int,
    ) -> CouponSaveModel:
        data = CouponSaveModel(
            coupon=self.generate_coupon_code(),
            percent=discount,
            created=utc_now_naive(),
            expiration=utc_now_naive() + timedelta(days=days_valid),
        )
        return data

    async def update_coupon_times_used(self, coupon_code: str) -> None:
        await self.repo.update_coupon_times_used(coupon_code=coupon_code)

    async def check_coupon(
            self,
            coupon_code: str,
            tariff: str | None = None,
    ) -> CouponCheckModel | None:
        if not coupon_code:
            return None

        if not re.search(r"^[a-zA-Z0-9]{3,20}$", coupon_code):
            return None

        coupon_db = await self.repo.get_coupon_by_code(coupon_code)
        if not coupon_db:
            return None

        if coupon_db.plans and tariff:
            if int(tariff) not in [int(pl) for pl in coupon_db.plans.split(",")]:
                return None

        if coupon_db.max_use_limit and coupon_db.times_used and coupon_db.times_used >= coupon_db.max_use_limit:
            return None

        if coupon_db.expiration < datetime.now(UTC):
            return None

        return CouponCheckModel(
            percent=coupon_db.percent,
            prolong=coupon_db.prolong,
        )


def get_coupon_service(
        repo: CouponDBRepo = Depends(get_coupon_repo),  # noqa: B008
) -> CouponService:
    return CouponService(repo)
