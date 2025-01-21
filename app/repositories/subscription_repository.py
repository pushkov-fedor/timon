from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self, db: Session):
        super().__init__(Subscription, db)

    def get_active_by_channel_id(self, channel_id: int) -> list[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(
                and_(
                    Subscription.channel_id == channel_id,
                    Subscription.is_active == True
                )
            )
            .all()
        )

    def get_by_channel_and_callback(
        self, 
        channel_id: int, 
        callback_url: str
    ) -> Subscription | None:
        return (
            self.db.query(Subscription)
            .filter(
                and_(
                    Subscription.channel_id == channel_id,
                    Subscription.callback_url == callback_url
                )
            )
            .first()
        )

    def get(self, subscription_id: int) -> Subscription | None:
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def create(self, subscription: Subscription) -> Subscription:
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update(self, subscription: Subscription) -> Subscription:
        """Update subscription in database"""
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def delete(self, subscription: Subscription) -> None:
        """Physically delete subscription from database"""
        self.db.delete(subscription)
        self.db.commit() 