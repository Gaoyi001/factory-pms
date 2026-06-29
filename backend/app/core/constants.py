from enum import Enum


class InventoryStatus(str, Enum):
    NORMAL = "normal"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"


class TransactionType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BORROW = "borrow"
    RETURN = "return_transfer"
    CHECK = "check"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    ADJUST = "adjust"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class AlertType(str, Enum):
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRY = "expiry"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class ProjectStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    RELEASED = "released"
    ARCHIVED = "archived"


class AlertReadStatus(int, Enum):
    UNREAD = 0
    READ = 1


class AlertResolveStatus(int, Enum):
    UNRESOLVED = 0
    RESOLVED = 1


TX_TYPE_DISPLAY = {
    TransactionType.INBOUND: "入库",
    TransactionType.OUTBOUND: "出库",
    TransactionType.BORROW: "领用",
    TransactionType.RETURN: "归还",
    TransactionType.CHECK: "盘点",
    TransactionType.TRANSFER_IN: "调拨入库",
    TransactionType.TRANSFER_OUT: "调拨出库",
    TransactionType.ADJUST: "调整",
}


INVENTORY_STATUS_DISPLAY = {
    InventoryStatus.NORMAL: "正常",
    InventoryStatus.LOW_STOCK: "库存不足",
    InventoryStatus.OUT_OF_STOCK: "库存耗尽",
    InventoryStatus.EXPIRED: "已过期",
}


APPROVAL_STATUS_DISPLAY = {
    ApprovalStatus.PENDING: "待审批",
    ApprovalStatus.APPROVED: "已通过",
    ApprovalStatus.REJECTED: "已拒绝",
    ApprovalStatus.COMPLETED: "已完成",
}