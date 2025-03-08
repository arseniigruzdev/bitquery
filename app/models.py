from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TokenBase(BaseModel):
    token_address: str
    token_name: Optional[str] = None
    token_symbol: Optional[str] = None
    creator_address: str
    creation_time: datetime

class TokenCreate(TokenBase):
    pass

class Token(TokenBase):
    id: int
    market_cap: Optional[float] = None
    price: Optional[float] = None
    volume_24h: Optional[float] = None
    holders_count: Optional[int] = None
    bonding_curve_progress: Optional[float] = None
    is_king_of_hill: bool = False
    king_of_hill_time: Optional[datetime] = None
    raydium_migrated: bool = False
    raydium_migration_time: Optional[datetime] = None
    highest_market_cap: Optional[float] = None
    highest_market_cap_time: Optional[datetime] = None
    last_updated: datetime

    class Config:
        orm_mode = True

class DeveloperBase(BaseModel):
    wallet_address: str
    first_seen: datetime

class DeveloperCreate(DeveloperBase):
    pass

class Developer(DeveloperBase):
    id: int
    tokens_created: int = 0
    successful_tokens: int = 0
    king_of_hill_tokens: int = 0
    raydium_migrated_tokens: int = 0
    total_volume_generated: float = 0
    highest_mcap_token: Optional[str] = None
    highest_mcap_value: Optional[float] = None
    last_token_created: Optional[datetime] = None
    last_updated: datetime

    class Config:
        orm_mode = True

class DeveloperWithTokens(Developer):
    tokens: List[Token] = []
