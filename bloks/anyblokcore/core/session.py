from AnyBlok import target_registry, Core
from sqlalchemy.orm import Session


target_registry(Core, name='Session', cls_=Session)
