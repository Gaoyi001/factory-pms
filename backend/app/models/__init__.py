# app/models/__init__.py
# 导入所有模型以确保它们被 SQLAlchemy 注册
from app.models.user import User, Department
from app.models.project import Project, ProjectType, Task, Requirement
from app.models.experiment import Experiment, ExperimentRecord, ExperimentAttachment
from app.models.bom import Material, BomHeader, BomItem, BomChange
from app.models.sample import Sample, SampleInspection, SampleInspectionItem, TrialProduction
from app.models.document import Document, DocumentVersion, DocumentApproval, DocCategory, KnowledgeArticle
from app.models.role import Role, Permission
from app.models.operation_log import OperationLog
from app.models.inventory import InventoryItem, InventoryTransaction, InventoryApproval, InventoryAlert, Warehouse

__all__ = [
    "User", "Department",
    "Project", "ProjectType", "Task", "Requirement",
    "Experiment", "ExperimentRecord", "ExperimentAttachment",
    "Material", "BomHeader", "BomItem", "BomChange",
    "Sample", "SampleInspection", "SampleInspectionItem", "TrialProduction",
    "Document", "DocumentVersion", "DocumentApproval", "DocCategory", "KnowledgeArticle",
    "Role", "Permission",
    "OperationLog",
    "InventoryItem", "InventoryTransaction", "InventoryApproval", "InventoryAlert", "Warehouse",
]
