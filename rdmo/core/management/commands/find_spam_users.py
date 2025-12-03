"""Management command to flag potentially automated or spam user accounts."""

from __future__ import annotations

import csv
from datetime import datetime
from itertools import accumulate, groupby
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from rdmo.projects.models import Membership


DateTuple = Tuple[int, str, str, str, datetime, str, Optional[datetime]]
UserRow = Dict[str, object]


class Command(BaseCommand):
    help = (
        "Find potentially automated/spam users by detecting many users that joined in quick succession. "
        "Optionally write results to CSV for further inspection."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-t",
            "--timespan",
            default=2,
            type=int,
            help=(
                "timespan in seconds between two joining users, "
                "less than the given value is considered to be suspicious, "
                "default is 2"
            ),
        )
        parser.add_argument(
            "-n",
            "--occurrence",
            default=3,
            type=int,
            help=(
                "number of sequentially occurring timespan violations at which users are put into the "
                "potential spam users list, default is 3"
            ),
        )
        parser.add_argument(
            "-p",
            "--print",
            action="store_true",
            help="print found users, don't save them to csv",
        )
        parser.add_argument(
            "-o",
            "--output_file",
            default="potential_spam_users.csv",
            help='output file, default is "potential_spam_users.csv"',
        )

    def save_csv(self, data: Iterable[UserRow], filename: str) -> None:
        """Write the provided rows to a CSV file if there is data to persist."""

        rows = list(data)
        if not rows:
            self.stdout.write("No data to write.")
            return

        keys = list(rows[0].keys())
        with open(filename, "w", newline="", encoding="utf-8") as data_file:
            csv_writer = csv.DictWriter(data_file, fieldnames=keys)
            csv_writer.writeheader()
            csv_writer.writerows(rows)
        self.stdout.write(f"List written to {filename}")

    def print_file(self, filename: str) -> None:
        with open(filename) as file:
            self.stdout.write(file.read())

    def get_users_having_projects(self) -> Set[int]:
        """Return a set of user ids that belong to at least one project."""

        return set(Membership.objects.values_list("user", flat=True))

    def _date_string(self, value: Optional[datetime]) -> Optional[str]:
        if not value:
            return None
        return value.strftime("%Y-%m-%dT%H:%M:%S.%f")

    def _normalize_datetime(self, value: datetime) -> datetime:
        """Ensure datetimes are timezone-aware to avoid timestamp errors."""

        return timezone.make_aware(value) if timezone.is_naive(value) else value

    def _user_queryset(self) -> Sequence[DateTuple]:
        return User.objects.order_by("date_joined").values_list(
            "id", "username", "first_name", "last_name", "date_joined", "email", "last_login"
        )

    def _rows_from_user_values(self, user_rows: Sequence[DateTuple], users_with_projects: Set[int]) -> List[UserRow]:
        rows: List[UserRow] = []
        for uid, username, first_name, last_name, date_joined, email, last_login in user_rows:
            aware_joined = self._normalize_datetime(date_joined)
            rows.append(
                {
                    "id": uid,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "date_joined": aware_joined,
                    "unix_joined": aware_joined.timestamp(),
                    "email": email,
                    "last_login": last_login,
                    "has_project": uid in users_with_projects,
                }
            )
        return rows

    def _group_users(self, users: Sequence[UserRow], timespan: int) -> Dict[int, List[UserRow]]:
        """Group users into sequential buckets separated by at least ``timespan`` seconds."""

        markers = [0]
        for previous, current in zip(users, users[1:]):
            gap = current["unix_joined"] - previous["unix_joined"]
            markers.append(1 if gap >= timespan else 0)

        group_ids = accumulate(markers)
        paired = zip(group_ids, users)

        return {gid: [user for _, user in items] for gid, items in groupby(paired, key=lambda pair: pair[0])}

    def _flatten_suspicious_groups(self, grouped_users: Dict[int, List[UserRow]], occurrence: int) -> List[UserRow]:
        """Flatten groups that exceed the occurrence threshold."""

        suspicious_groups = [
            (gid, group) for gid, group in grouped_users.items() if len(group) > occurrence
        ]

        potential_users: List[UserRow] = []
        for gid, members in suspicious_groups:
            group_size = len(members)
            if not group_size:
                continue

            start, end = members[0]["unix_joined"], members[-1]["unix_joined"]
            duration = round(end - start, 3) if group_size > 1 else 0

            for member in members:
                potential_users.append(
                    {
                        "id": member["id"],
                        "email": member["email"],
                        "username": member["username"],
                        "first_name": member["first_name"],
                        "last_name": member["last_name"],
                        "date_joined": self._date_string(member["date_joined"]),
                        "last_login": self._date_string(member["last_login"]),
                        "has_project": member["has_project"],
                        "group_id": gid,
                        "group_size": group_size,
                        "group_duration_seconds": duration,
                    }
                )

        return potential_users

    def find_potential_spam_users(self, timespan: int, occurrence: int):
        users_with_projects = self.get_users_having_projects()
        raw_users = self._user_queryset()
        user_rows = self._rows_from_user_values(raw_users, users_with_projects)

        if not user_rows:
            return [], 0, len(users_with_projects), 0

        grouped_users = self._group_users(user_rows, timespan)
        potential_spam_users = self._flatten_suspicious_groups(grouped_users, occurrence)

        potential_with_projects = sum(1 for user in potential_spam_users if user["has_project"])
        return potential_spam_users, len(user_rows), len(users_with_projects), potential_with_projects

    def handle(self, *args, **options):
        total_users = User.objects.count()
        self.stdout.write(f"Total number of users: {total_users}")

        potential_spam_users, pool_size, users_with_projects, potential_with_projects = self.find_potential_spam_users(
            options["timespan"], options["occurrence"]
        )

        percentage_of_pool = (100 * len(potential_spam_users) / pool_size) if pool_size else 0
        percentage_of_total = (100 * len(potential_spam_users) / total_users) if total_users else 0

        self.stdout.write(
            "Potential spam users: "
            f"{len(potential_spam_users)} [{percentage_of_pool:.2f}% of pool, {percentage_of_total:.2f}% of total]"
        )
        self.stdout.write(
            "Potential spam users having at least one project: "
            f"{potential_with_projects} / Total users with at least one project: {users_with_projects}"
        )

        self.save_csv(potential_spam_users, options["output_file"])
        if options["print"]:
            self.print_file(options["output_file"])
