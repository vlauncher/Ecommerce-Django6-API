from .models import User, UserProfile


def get_user_by_email(email: str) -> User | None:
    """
    Fetch a User instance by email (synchronous).
    """
    try:
        return User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return None


async def aget_user_by_email(email: str) -> User | None:
    """
    Fetch a User instance by email (asynchronous).
    """
    try:
        return await User.objects.aget(email__iexact=email)
    except User.DoesNotExist:
        return None


async def aget_user_by_id(user_id: int) -> User | None:
    """
    Fetch a User instance by ID (asynchronous).
    """
    try:
        return await User.objects.aget(id=user_id)
    except User.DoesNotExist:
        return None


def get_profile_by_user(user: User) -> UserProfile:
    """
    Fetch or get UserProfile for a User instance (synchronous).
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


async def aget_profile_by_user(user: User) -> UserProfile:
    """
    Fetch or get UserProfile for a User instance (asynchronous).
    """
    try:
        return await UserProfile.objects.select_related("user").aget(user=user)
    except UserProfile.DoesNotExist:
        return await UserProfile.objects.acreate(user=user)
