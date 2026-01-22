import datetime
from typing import List

from querymate.core.querymate import Querymate

from vibeify_api.models.enums import ReviewItemType
from vibeify_api.models.review_item import ReviewItem
from vibeify_api.services import BaseService


class ReviewItemsService(BaseService[ReviewItem]):

    def __init__(self):
        super().__init__(ReviewItem)

    async def get_review_item_assignment(
            self,
            search_text: str,
            offset: int,
            review_item_type: ReviewItemType,
            target_app: str
    ) -> List[ReviewItem]:
        """ Gets a task assignment for the current user. Unsets any existing
        locks on tasks, retrieves a single task and "locks" it to the current user
        for 30 minutes.

        :param search_text: the search text to filter on
        :param review_item_type: the task type to filter on
        :param offset: the offset to start from
        :return:
        """
        current_user = self.require_current_user()

        await self.repository.run_sql_statement(
            "UPDATE review_items SET user_id = NULL, lock_datetime = NULL WHERE user_id = :user_id AND completed_datetime IS NULL",
            parameters={"user_id": current_user.id}
        )

        self._logger.debug(f"Unlocked review item for user {current_user.id}")

        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=30)

        query_filter = {
            "and": [
                {
                    "or": [
                        {"user_id": {"eq": None}},
                        {"lock_datetime": {"gte": cutoff}}
                    ]
                },
                {
                    "completed_datetime": {"eq": None}
                }
        ]}

        if review_item_type is not None:
            query_filter["and"].append({"review_item_type": {"eq": review_item_type.value}})

        if search_text is not None:
            query_filter["and"].append({"name": {"cont": search_text}})

        if target_app is not None:
            query_filter["and"].append({"target_app": {"eq": target_app}})

        new_review_item_assignment = await self.repository.query_raw(
                query=Querymate(filter=query_filter,
                limit=1,
                offset=offset
            )
        )

        if new_review_item_assignment is None or len(new_review_item_assignment) == 0:
            return []
        else:
            await self.repository.update(
                new_review_item_assignment[0].id,
                {"user_id": current_user.id, "lock_datetime": datetime.datetime.now()}
            )
            return new_review_item_assignment
