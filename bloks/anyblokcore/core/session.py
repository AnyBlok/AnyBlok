from anyblok import AnyBlok
from sqlalchemy.orm import Session


AnyBlok.target_registry(AnyBlok.Core, name='Session', cls_=Session)
