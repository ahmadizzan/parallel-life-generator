import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class ContextBlock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    role: str  # E.g., 'system', 'user', 'assistant'

    decision_id: Optional[int] = Field(default=None, foreign_key="decision.id")
    decision: Optional["Decision"] = Relationship(back_populates="context_blocks")


class Decision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    summary: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None)  # JSON string for tags
    tradeoffs: Optional[str] = Field(default=None)  # JSON string for tradeoffs
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow, nullable=False
    )

    context_blocks: List[ContextBlock] = Relationship(back_populates="decision")
    branch_nodes: List["BranchNode"] = Relationship(back_populates="decision")


class BranchNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Key to the Decision that this node represents
    decision_id: Optional[int] = Field(default=None, foreign_key="decision.id")
    decision: Optional["Decision"] = Relationship(back_populates="branch_nodes")

    # Self-referential relationship to build the tree
    parent_id: Optional[int] = Field(default=None, foreign_key="branchnode.id")
    parent: Optional["BranchNode"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs=dict(remote_side="BranchNode.id"),
    )
    children: List["BranchNode"] = Relationship(back_populates="parent")
