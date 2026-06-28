"""
Factory PMS - 录入异常/参数校验测试脚本
用法: python test_validation.py
覆盖: 各模块的非法输入均被后端正确拒绝（422/400），并返回可读的中文错误提示
依赖: requests （pip install requests）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# ========== 测试结果统计 ==========
passed = 0
failed = 0
results = []


def test(name, func):
    """执行一个测试用例"""
    global passed, failed
    try:
        func()
        passed += 1
        results.append(f"  PASS {name}")
        print(f"  PASS {name}")
    except AssertionError as e:
        failed += 1
        results.append(f"  FAIL {name}: {e}")
        print(f"  FAIL {name}: {e}")
    except Exception as e:
        failed += 1
        results.append(f"  FAIL {name}: {type(e).__name__}: {e}")
        print(f"  FAIL {name}: {type(e).__name__}: {e}")


def assert_in(item, container, msg=""):
    if item not in container:
        raise AssertionError(f"{msg} expected '{item}' in {container}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


def assert_status(resp, expected, msg=""):
    """断言响应状态码（expected 可为单个值或元组）"""
    codes = expected if isinstance(expected, tuple) else (expected,)
    if resp.status_code not in codes:
        raise AssertionError(
            f"{msg} expected status {expected}, got {resp.status_code}: {resp.text[:200]}"
        )


def assert_validation_error(resp, msg=""):
    """断言为参数校验错误（422）"""
    assert_status(resp, 422, msg)
    body = resp.json()
    # 后端统一返回 code/message/detail 结构
    assert_true(
        body.get("code") == 422 or "detail" in body or "message" in body,
        f"{msg} 响应体未包含校验错误信息: {body}"
    )


# ========== API 客户端 ==========
class ApiClient:
    def __init__(self):
        self.token = None
        self.headers = {}

    def login(self, username, password):
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "username": username, "password": password
        })
        if r.status_code == 200:
            data = r.json()
            self.token = data["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        return r

    def get(self, path, **kwargs):
        return requests.get(f"{BASE_URL}{path}", headers=self.headers, **kwargs)

    def post(self, path, json_data=None, **kwargs):
        return requests.post(f"{BASE_URL}{path}", json=json_data, headers=self.headers, **kwargs)

    def put(self, path, json_data=None, **kwargs):
        return requests.put(f"{BASE_URL}{path}", json=json_data, headers=self.headers, **kwargs)


client = ApiClient()


# ========== 1. 认证模块校验 ==========
def test_auth_validation():
    print("\n[1] 认证模块 - 录入校验")

    def test_login_empty_body():
        r = requests.post(f"{BASE_URL}/auth/login", json={})
        assert_validation_error(r, "空请求体应返回422")

    def test_login_missing_password():
        r = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin"})
        assert_validation_error(r, "缺少密码应返回422")

    def test_login_missing_username():
        r = requests.post(f"{BASE_URL}/auth/login", json={"password": "123456"})
        assert_validation_error(r, "缺少用户名应返回422")

    def test_me_without_token():
        r = requests.get(f"{BASE_URL}/auth/me")
        assert_status(r, 401, "无Token访问应返回401")

    test("登录-空请求体", test_login_empty_body)
    test("登录-缺少密码", test_login_missing_password)
    test("登录-缺少用户名", test_login_missing_username)
    test("无Token访问受保护接口", test_me_without_token)


# ========== 2. 部门管理校验 ==========
def test_department_validation():
    print("\n[2] 部门管理 - 录入校验")

    def test_create_dept_missing_name():
        r = client.post("/departments/create", {"parent_id": None})
        assert_validation_error(r, "缺少部门名称应返回422")

    def test_create_dept_name_too_short():
        r = client.post("/departments/create", {"name": "a", "parent_id": None})
        assert_validation_error(r, "部门名称过短(<2)应返回422")

    def test_create_dept_name_too_long():
        r = client.post("/departments/create", {"name": "x" * 101, "parent_id": None})
        assert_validation_error(r, "部门名称过长(>100)应返回422")

    def test_create_dept_empty_name():
        r = client.post("/departments/create", {"name": "", "parent_id": None})
        assert_validation_error(r, "空部门名称应返回422")

    def test_get_nonexistent_dept():
        r = client.get("/departments/9999999")
        assert_status(r, 404, "不存在的部门应返回404")

    test("创建部门-缺少名称", test_create_dept_missing_name)
    test("创建部门-名称过短", test_create_dept_name_too_short)
    test("创建部门-名称过长", test_create_dept_name_too_long)
    test("创建部门-空名称", test_create_dept_empty_name)
    test("查询-不存在的部门", test_get_nonexistent_dept)


# ========== 3. 角色管理校验 ==========
def test_role_validation():
    print("\n[3] 角色管理 - 录入校验")

    def test_create_role_missing_code():
        r = client.post("/roles/create", {"name": "测试角色"})
        assert_validation_error(r, "缺少角色编码应返回422")

    def test_create_role_missing_name():
        r = client.post("/roles/create", {"code": "test_code"})
        assert_validation_error(r, "缺少角色名称应返回422")

    def test_create_role_code_too_short():
        r = client.post("/roles/create", {"code": "a", "name": "短编码角色"})
        assert_validation_error(r, "角色编码过短(<2)应返回422")

    def test_create_role_code_too_long():
        r = client.post("/roles/create", {"code": "x" * 33, "name": "长编码角色"})
        assert_validation_error(r, "角色编码过长(>32)应返回422")

    def test_create_role_name_too_short():
        r = client.post("/roles/create", {"code": "validcode", "name": "a"})
        assert_validation_error(r, "角色名称过短(<2)应返回422")

    def test_get_nonexistent_role():
        r = client.get("/roles/9999999")
        assert_status(r, 404, "不存在的角色应返回404")

    test("创建角色-缺少编码", test_create_role_missing_code)
    test("创建角色-缺少名称", test_create_role_missing_name)
    test("创建角色-编码过短", test_create_role_code_too_short)
    test("创建角色-编码过长", test_create_role_code_too_long)
    test("创建角色-名称过短", test_create_role_name_too_short)
    test("查询-不存在的角色", test_get_nonexistent_role)


# ========== 4. 用户管理校验 ==========
def test_user_validation():
    print("\n[4] 用户管理 - 录入校验")

    def test_create_user_missing_username():
        r = client.post("/users/create", {
            "password": "test123456", "email": "test@x.com"
        })
        assert_validation_error(r, "缺少用户名应返回422")

    def test_create_user_username_too_short():
        r = client.post("/users/create", {
            "username": "ab", "password": "test123456", "email": "t@x.com"
        })
        assert_validation_error(r, "用户名过短(<3)应返回422")

    def test_create_user_username_too_long():
        r = client.post("/users/create", {
            "username": "x" * 65, "password": "test123456", "email": "t@x.com"
        })
        assert_validation_error(r, "用户名过长(>64)应返回422")

    def test_create_user_missing_password():
        r = client.post("/users/create", {
            "username": "validuser", "email": "t@x.com"
        })
        assert_validation_error(r, "缺少密码应返回422")

    def test_create_user_password_too_short():
        r = client.post("/users/create", {
            "username": "validuser", "password": "12345", "email": "t@x.com"
        })
        assert_validation_error(r, "密码过短(<6)应返回422")

    def test_create_user_invalid_email():
        r = client.post("/users/create", {
            "username": "validuser", "password": "test123456", "email": "not-an-email"
        })
        assert_validation_error(r, "非法邮箱格式应返回422")

    def test_create_user_missing_email():
        r = client.post("/users/create", {
            "username": "validuser", "password": "test123456"
        })
        assert_validation_error(r, "缺少邮箱应返回422")

    def test_create_user_invalid_role():
        r = client.post("/users/create", {
            "username": "validuser", "password": "test123456",
            "email": "t@x.com", "role": "superadmin"
        })
        assert_validation_error(r, "非法角色值应返回422")

    def test_change_password_too_short():
        r = client.post("/users/change-password", {
            "new_password": "12345"
        })
        assert_validation_error(r, "新密码过短(<6)应返回422")

    def test_change_password_missing():
        r = client.post("/users/change-password", {})
        assert_validation_error(r, "缺少新密码应返回422")

    test("创建用户-缺少用户名", test_create_user_missing_username)
    test("创建用户-用户名过短", test_create_user_username_too_short)
    test("创建用户-用户名过长", test_create_user_username_too_long)
    test("创建用户-缺少密码", test_create_user_missing_password)
    test("创建用户-密码过短", test_create_user_password_too_short)
    test("创建用户-非法邮箱", test_create_user_invalid_email)
    test("创建用户-缺少邮箱", test_create_user_missing_email)
    test("创建用户-非法角色", test_create_user_invalid_role)
    test("修改密码-密码过短", test_change_password_too_short)
    test("修改密码-缺少新密码", test_change_password_missing)


# ========== 5. 项目管理校验 ==========
def test_project_validation():
    print("\n[5] 项目管理 - 录入校验")

    def test_create_project_missing_name():
        r = client.post("/projects/create", {"priority": 3, "status": "draft"})
        assert_validation_error(r, "缺少项目名称应返回422")

    def test_create_project_name_too_long():
        r = client.post("/projects/create", {"name": "x" * 201, "status": "draft"})
        assert_validation_error(r, "项目名称过长(>200)应返回422")

    def test_create_project_invalid_status():
        r = client.post("/projects/create", {
            "name": "测试项目", "status": "invalid_status"
        })
        # 自定义 model_validator 抛 ValueError -> 422
        assert_validation_error(r, "非法项目状态应返回422")

    def test_create_project_priority_too_high():
        r = client.post("/projects/create", {
            "name": "测试项目", "status": "draft", "priority": 6
        })
        assert_validation_error(r, "优先级>5应返回422")

    def test_create_project_priority_too_low():
        r = client.post("/projects/create", {
            "name": "测试项目", "status": "draft", "priority": 0
        })
        assert_validation_error(r, "优先级<1应返回422")

    def test_create_project_priority_not_int():
        r = client.post("/projects/create", {
            "name": "测试项目", "status": "draft", "priority": "abc"
        })
        assert_validation_error(r, "优先级非整数应返回422")

    def test_create_project_date_logic_error():
        r = client.post("/projects/create", {
            "name": "日期错误项目", "status": "draft",
            "plan_start": "2026-06-30", "plan_end": "2026-06-01"
        })
        # 自定义校验：开始日期不能晚于结束日期
        assert_validation_error(r, "开始日期晚于结束日期应返回422")

    def test_create_project_invalid_date_format():
        r = client.post("/projects/create", {
            "name": "日期格式错误", "status": "draft",
            "plan_start": "2026/06/30"
        })
        assert_validation_error(r, "非法日期格式应返回422")

    def test_get_nonexistent_project():
        r = client.get("/projects/9999999")
        assert_status(r, 404, "不存在的项目应返回404")

    test("创建项目-缺少名称", test_create_project_missing_name)
    test("创建项目-名称过长", test_create_project_name_too_long)
    test("创建项目-非法状态", test_create_project_invalid_status)
    test("创建项目-优先级过高", test_create_project_priority_too_high)
    test("创建项目-优先级过低", test_create_project_priority_too_low)
    test("创建项目-优先级非整数", test_create_project_priority_not_int)
    test("创建项目-日期逻辑错误", test_create_project_date_logic_error)
    test("创建项目-非法日期格式", test_create_project_invalid_date_format)
    test("查询-不存在的项目", test_get_nonexistent_project)


# ========== 6. 实验管理校验 ==========
def test_experiment_validation():
    print("\n[6] 实验管理 - 录入校验")

    def test_create_experiment_missing_name():
        r = client.post("/experiments/create", {"project_id": 1})
        assert_validation_error(r, "缺少实验名称应返回422")

    def test_create_experiment_missing_project_id():
        r = client.post("/experiments/create", {"name": "测试实验"})
        assert_validation_error(r, "缺少项目ID应返回422")

    def test_create_experiment_name_too_long():
        r = client.post("/experiments/create", {
            "name": "x" * 201, "project_id": 1
        })
        assert_validation_error(r, "实验名称过长(>200)应返回422")

    def test_create_experiment_project_id_not_int():
        r = client.post("/experiments/create", {
            "name": "测试实验", "project_id": "abc"
        })
        assert_validation_error(r, "项目ID非整数应返回422")

    def test_create_record_missing_experiment_id():
        r = client.post("/experiments/records", {"batch_no": "B001"})
        assert_validation_error(r, "缺少实验ID应返回422")

    test("创建实验-缺少名称", test_create_experiment_missing_name)
    test("创建实验-缺少项目ID", test_create_experiment_missing_project_id)
    test("创建实验-名称过长", test_create_experiment_name_too_long)
    test("创建实验-项目ID非整数", test_create_experiment_project_id_not_int)
    test("创建实验记录-缺少实验ID", test_create_record_missing_experiment_id)


# ========== 7. BOM管理校验 ==========
def test_bom_validation():
    print("\n[7] BOM管理 - 录入校验")

    def test_create_material_missing_code():
        r = client.post("/bom/materials", {"name": "测试物料"})
        assert_validation_error(r, "缺少物料编码应返回422")

    def test_create_material_missing_name():
        r = client.post("/bom/materials", {"code": "M001"})
        assert_validation_error(r, "缺少物料名称应返回422")

    def test_create_material_code_too_long():
        r = client.post("/bom/materials", {"code": "x" * 65, "name": "物料"})
        assert_validation_error(r, "物料编码过长(>64)应返回422")

    def test_create_material_name_too_long():
        r = client.post("/bom/materials", {"code": "M001", "name": "x" * 201})
        assert_validation_error(r, "物料名称过长(>200)应返回422")

    def test_create_bom_missing_name():
        r = client.post("/bom/headers", {"version": "V1.0"})
        assert_validation_error(r, "缺少BOM名称应返回422")

    def test_create_bom_name_too_long():
        r = client.post("/bom/headers", {"name": "x" * 201})
        assert_validation_error(r, "BOM名称过长(>200)应返回422")

    def test_create_bom_change_missing_bom_id():
        r = client.post("/bom/changes", {
            "change_type": "material_replace", "title": "变更单"
        })
        assert_validation_error(r, "缺少BOM ID应返回422")

    def test_create_bom_change_missing_title():
        r = client.post("/bom/changes", {
            "change_type": "material_replace", "bom_id": 1
        })
        assert_validation_error(r, "缺少变更标题应返回422")

    def test_create_bom_change_missing_change_type():
        r = client.post("/bom/changes", {"title": "变更单", "bom_id": 1})
        assert_validation_error(r, "缺少变更类型应返回422")

    test("创建物料-缺少编码", test_create_material_missing_code)
    test("创建物料-缺少名称", test_create_material_missing_name)
    test("创建物料-编码过长", test_create_material_code_too_long)
    test("创建物料-名称过长", test_create_material_name_too_long)
    test("创建BOM-缺少名称", test_create_bom_missing_name)
    test("创建BOM-名称过长", test_create_bom_name_too_long)
    test("创建BOM变更-缺少BOM ID", test_create_bom_change_missing_bom_id)
    test("创建BOM变更-缺少标题", test_create_bom_change_missing_title)
    test("创建BOM变更-缺少变更类型", test_create_bom_change_missing_change_type)


# ========== 8. 样品试产校验 ==========
def test_sample_validation():
    print("\n[8] 样品试产 - 录入校验")

    def test_create_sample_missing_name():
        r = client.post("/samples/samples", {"project_id": 1})
        assert_validation_error(r, "缺少样品名称应返回422")

    def test_create_sample_missing_project_id():
        r = client.post("/samples/samples", {"name": "测试样品"})
        assert_validation_error(r, "缺少项目ID应返回422")

    def test_create_sample_name_too_long():
        r = client.post("/samples/samples", {"name": "x" * 201, "project_id": 1})
        assert_validation_error(r, "样品名称过长(>200)应返回422")

    def test_create_inspection_missing_sample_id():
        r = client.post("/samples/inspections", {"inspect_type": "dimension"})
        assert_validation_error(r, "缺少样品ID应返回422")

    def test_create_inspection_missing_inspect_type():
        r = client.post("/samples/inspections", {"sample_id": 1})
        assert_validation_error(r, "缺少检验类型应返回422")

    def test_create_trial_missing_name():
        r = client.post("/samples/trials", {"project_id": 1})
        assert_validation_error(r, "缺少试产名称应返回422")

    def test_create_trial_missing_project_id():
        r = client.post("/samples/trials", {"name": "试产"})
        assert_validation_error(r, "缺少项目ID应返回422")

    def test_create_trial_name_too_long():
        r = client.post("/samples/trials", {"name": "x" * 201, "project_id": 1})
        assert_validation_error(r, "试产名称过长(>200)应返回422")

    test("创建样品-缺少名称", test_create_sample_missing_name)
    test("创建样品-缺少项目ID", test_create_sample_missing_project_id)
    test("创建样品-名称过长", test_create_sample_name_too_long)
    test("创建检验-缺少样品ID", test_create_inspection_missing_sample_id)
    test("创建检验-缺少检验类型", test_create_inspection_missing_inspect_type)
    test("创建试产-缺少名称", test_create_trial_missing_name)
    test("创建试产-缺少项目ID", test_create_trial_missing_project_id)
    test("创建试产-名称过长", test_create_trial_name_too_long)


# ========== 9. 文档知识校验 ==========
def test_document_validation():
    print("\n[9] 文档知识 - 录入校验")

    def test_create_doc_missing_title():
        r = client.post("/documents/create", {"doc_type": "design"})
        assert_validation_error(r, "缺少文档标题应返回422")

    def test_create_doc_title_too_long():
        r = client.post("/documents/create", {"title": "x" * 201})
        assert_validation_error(r, "文档标题过长(>200)应返回422")

    def test_get_nonexistent_doc():
        r = client.get("/documents/9999999")
        assert_status(r, 404, "不存在的文档应返回404")

    def test_get_nonexistent_knowledge():
        r = client.get("/documents/knowledge/9999999")
        assert_status(r, 404, "不存在的知识文章应返回404")

    test("创建文档-缺少标题", test_create_doc_missing_title)
    test("创建文档-标题过长", test_create_doc_title_too_long)
    test("查询-不存在的文档", test_get_nonexistent_doc)
    test("查询-不存在的知识文章", test_get_nonexistent_knowledge)


# ========== 10. 库存管理校验 ==========
def test_inventory_validation():
    print("\n[10] 库存管理 - 录入校验")

    def test_create_inventory_missing_material_id():
        r = client.post("/inventory/create", {"warehouse": "主仓库"})
        assert_validation_error(r, "缺少物料ID应返回422")

    def test_create_inventory_missing_warehouse():
        r = client.post("/inventory/create", {"material_id": 1})
        assert_validation_error(r, "缺少仓库应返回422")

    def test_create_inventory_warehouse_too_long():
        r = client.post("/inventory/create", {
            "material_id": 1, "warehouse": "x" * 101
        })
        assert_validation_error(r, "仓名过长(>100)应返回422")

    def test_create_transaction_missing_item_id():
        r = client.post("/inventory/inbound", {
            "transaction_type": "inbound", "quantity": 10
        })
        assert_validation_error(r, "缺少库存项ID应返回422")

    def test_create_transaction_missing_type():
        r = client.post("/inventory/inbound", {
            "inventory_item_id": 1, "quantity": 10
        })
        assert_validation_error(r, "缺少交易类型应返回422")

    def test_create_transaction_missing_quantity():
        r = client.post("/inventory/inbound", {
            "inventory_item_id": 1, "transaction_type": "inbound"
        })
        assert_validation_error(r, "缺少数量应返回422")

    def test_create_warehouse_missing_name():
        r = client.post("/inventory/warehouses/create", {"code": "WH01"})
        assert_validation_error(r, "缺少仓库名称应返回422")

    def test_create_warehouse_missing_code():
        r = client.post("/inventory/warehouses/create", {"name": "新仓库"})
        assert_validation_error(r, "缺少仓库编码应返回422")

    def test_create_warehouse_name_too_long():
        r = client.post("/inventory/warehouses/create", {
            "name": "x" * 101, "code": "WH01"
        })
        assert_validation_error(r, "仓库名称过长(>100)应返回422")

    test("创建库存-缺少物料ID", test_create_inventory_missing_material_id)
    test("创建库存-缺少仓库", test_create_inventory_missing_warehouse)
    test("创建库存-仓名过长", test_create_inventory_warehouse_too_long)
    test("创建交易-缺少库存项ID", test_create_transaction_missing_item_id)
    test("创建交易-缺少交易类型", test_create_transaction_missing_type)
    test("创建交易-缺少数量", test_create_transaction_missing_quantity)
    test("创建仓库-缺少名称", test_create_warehouse_missing_name)
    test("创建仓库-缺少编码", test_create_warehouse_missing_code)
    test("创建仓库-名称过长", test_create_warehouse_name_too_long)


# ========== 11. 操作日志校验 ==========
def test_operation_log_validation():
    print("\n[11] 操作日志 - 录入校验")

    def test_cleanup_retention_too_small():
        r = client.post("/operation-logs/cleanup", {"retention_days": 6})
        assert_validation_error(r, "保留天数<7应返回422")

    def test_cleanup_retention_too_large():
        r = client.post("/operation-logs/cleanup", {"retention_days": 366})
        assert_validation_error(r, "保留天数>365应返回422")

    def test_cleanup_retention_not_int():
        r = client.post("/operation-logs/cleanup", {"retention_days": "abc"})
        assert_validation_error(r, "保留天数非整数应返回422")

    # 注：若清理接口未实现，该项会被标记失败而非跳过，便于发现接口缺口
    test("日志清理-保留天数过小", test_cleanup_retention_too_small)
    test("日志清理-保留天数过大", test_cleanup_retention_too_large)
    test("日志清理-保留天数非整数", test_cleanup_retention_not_int)


# ========== 主函数 ==========
def main():
    global passed, failed, results

    print("=" * 60)
    print("Factory PMS - 录入异常/参数校验测试")
    print("=" * 60)
    print(f"测试地址: {BASE_URL}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查服务是否可用
    try:
        requests.get(f"{BASE_URL}/auth/me", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] 无法连接到后端服务!")
        print("请先启动后端服务:")
        print("  cd backend")
        print("  python -m uvicorn app.main:app --port 8000")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n[WARN] 连接超时，服务可能正在启动")

    # 登录
    print("\n登录管理员账号...")
    r = client.login("admin", "admin123")
    if r.status_code != 200:
        print(f"[ERROR] 登录失败: {r.status_code} {r.text[:200]}")
        sys.exit(1)
    print("  登录成功")

    # 按模块执行校验测试
    test_auth_validation()
    test_department_validation()
    test_role_validation()
    test_user_validation()
    test_project_validation()
    test_experiment_validation()
    test_bom_validation()
    test_sample_validation()
    test_document_validation()
    test_inventory_validation()
    test_operation_log_validation()

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    total = passed + failed
    print(f"  总计: {total} 个用例")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    if total > 0:
        pct = passed / total * 100
        print(f"  通过率: {pct:.1f}%")
        if pct >= 95:
            print("  评级: 优秀 - 校验覆盖完善")
        elif pct >= 80:
            print("  评级: 良好 - 个别校验需补全")
        else:
            print("  评级: 需改进 - 校验存在缺口")

    if failed > 0:
        print("\n失败的用例:")
        for r in results:
            if "FAIL" in r:
                print(r)

    print("\n" + "=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
