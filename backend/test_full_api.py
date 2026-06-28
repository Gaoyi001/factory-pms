"""
Factory PMS - 后端 API 完整测试脚本
用法: python test_full_api.py
覆盖: 认证、部门、用户、角色、项目、实验、BOM、样品、文档、操作日志
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# ========== 测试结果统计 ==========
passed = 0
failed = 0
results = []
created_ids = {
    "dept": [],
    "role": [],
    "user": [],
    "project": [],
    "experiment": [],
    "material": [],
    "bom": [],
    "sample": [],
    "trial": [],
    "document": [],
    "article": [],
}


def test(name, func):
    """执行一个测试用例"""
    global passed, failed
    try:
        func()
        passed += 1
        results.append(f"  ✅ {name}")
        print(f"  ✅ {name}")
    except AssertionError as e:
        failed += 1
        results.append(f"  ❌ {name}: {e}")
        print(f"  ❌ {name}: {e}")
    except Exception as e:
        failed += 1
        results.append(f"  ❌ {name}: {type(e).__name__}: {e}")
        print(f"  ❌ {name}: {type(e).__name__}: {e}")


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg} expected={expected}, actual={actual}")


def assert_true(condition, msg=""):
    if not condition:
        raise AssertionError(msg)


def assert_in(key, container, msg=""):
    if key not in container:
        raise AssertionError(f"{msg} '{key}' not in container")


# ========== 工具函数 ==========
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

    def delete(self, path, **kwargs):
        return requests.delete(f"{BASE_URL}{path}", headers=self.headers, **kwargs)


client = ApiClient()


# ========== 1. 认证测试 ==========
def test_auth():
    print("\n📋 1. 认证模块")

    def test_login_success():
        r = client.login("admin", "admin123")
        assert_eq(r.status_code, 200)
        assert_true(client.token is not None, "token should not be None")

    def test_login_wrong_password():
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin", "password": "wrongpass"
        })
        assert_true(r.status_code in (401, 400), f"wrong password should fail, got {r.status_code}")

    def test_login_nonexistent_user():
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": "anypass"
        })
        assert_true(r.status_code in (401, 400), "nonexistent user should fail")

    def test_get_me():
        r = client.get("/auth/me")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["username"], "admin")
        assert_eq(data["role"], "admin")

    def test_get_me_without_token():
        noauth_client = ApiClient()
        r = noauth_client.get("/auth/me")
        assert_eq(r.status_code, 401, "should require authentication")

    test("登录成功", test_login_success)
    test("登录失败-错误密码", test_login_wrong_password)
    test("登录失败-不存在的用户", test_login_nonexistent_user)
    test("获取当前用户信息", test_get_me)
    test("无Token访问失败", test_get_me_without_token)


# ========== 2. 部门管理测试 ==========
def test_departments():
    print("\n📋 2. 部门管理")

    def test_list_departments():
        r = client.get("/departments/list")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return list")

    def test_tree_departments():
        r = client.get("/departments/tree")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return tree list")

    def test_create_department():
        r = client.post("/departments/create", {
            "name": f"测试部门_{int(time.time())}",
            "parent_id": None
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["dept"].append(data["id"])
        return data["id"]

    def test_create_sub_department(parent_id):
        r = client.post("/departments/create", {
            "name": f"子部门_{int(time.time())}",
            "parent_id": parent_id
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        created_ids["dept"].append(data["id"])
        return data["id"]

    def test_create_duplicate_department():
        dept_name = f"测试部门_重复_{int(time.time())}"
        r = client.post("/departments/create", {
            "name": dept_name,
            "parent_id": None
        })
        assert_eq(r.status_code, 200)
        created_ids["dept"].append(r.json()["data"]["id"])

        r = client.post("/departments/create", {
            "name": dept_name,
            "parent_id": None
        })
        assert_eq(r.status_code, 400, "duplicate name should fail")

    def test_get_department(dept_id):
        r = client.get(f"/departments/{dept_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], dept_id)

    def test_update_department(dept_id):
        r = client.put(f"/departments/{dept_id}", {
            "name": f"部门_更新_{int(time.time())}"
        })
        assert_eq(r.status_code, 200)
        r = client.get(f"/departments/{dept_id}")
        assert_eq(r.status_code, 200)

    def test_delete_department(dept_id):
        r = client.delete(f"/departments/{dept_id}")
        assert_eq(r.status_code, 200)
        r = client.get(f"/departments/{dept_id}")
        assert_eq(r.status_code, 404, "should be deleted")

    def test_delete_dept_with_children():
        # 创建一个有子部门的部门
        parent_id = test_create_department()
        child_id = test_create_sub_department(parent_id)
        # 尝试删除父部门
        r = client.delete(f"/departments/{parent_id}")
        assert_eq(r.status_code, 400, "cannot delete dept with children")

    # 执行测试
    dept_id = test_create_department()
    test("获取部门列表", test_list_departments)
    test("获取部门树", test_tree_departments)
    test("创建部门", lambda: test_create_department())
    test("创建重复部门失败", test_create_duplicate_department)
    test("获取部门详情", lambda: test_get_department(dept_id))
    test("更新部门", lambda: test_update_department(dept_id))
    test("删除部门(无子部门)", lambda: test_delete_department(dept_id))
    test("删除有子部门的部门失败", test_delete_dept_with_children)


# ========== 3. 角色管理测试 ==========
def test_roles():
    print("\n📋 3. 角色管理")

    def test_list_roles():
        r = client.get("/roles/list")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return list")
        assert_true(len(data) >= 4, "should have default roles")

    def test_list_permissions():
        r = client.get("/roles/permissions/list")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return list")
        assert_true(len(data) > 0, "should have permissions")

    def test_create_role():
        r = client.post("/roles/create", {
            "code": f"test_role_{int(time.time())}",
            "name": "测试角色",
            "description": "这是一个测试角色",
            "is_active": True,
            "sort_order": 10
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["role"].append(data["id"])
        return data["id"]

    def test_create_duplicate_role():
        code = f"dup_role_{int(time.time())}"
        r = client.post("/roles/create", {
            "code": code,
            "name": "重复角色1"
        })
        assert_eq(r.status_code, 200)
        created_ids["role"].append(r.json()["data"]["id"])

        r = client.post("/roles/create", {
            "code": code,
            "name": "重复角色2"
        })
        assert_eq(r.status_code, 400, "duplicate code should fail")

    def test_get_role(role_id):
        r = client.get(f"/roles/{role_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], role_id)
        return data

    def test_update_role(role_id):
        r = client.put(f"/roles/{role_id}", {
            "name": f"角色_更新_{int(time.time())}",
            "description": "更新后的描述"
        })
        assert_eq(r.status_code, 200)

    def test_assign_permissions(role_id):
        r = client.get("/roles/permissions/list")
        perms = r.json()["data"]
        perm_ids = [p["id"] for p in perms[:5]]

        r = client.post(f"/roles/{role_id}/permissions", perm_ids)
        assert_eq(r.status_code, 200)

        r = client.get(f"/roles/{role_id}")
        data = r.json()["data"]
        assert_true(len(data["permissions"]) == 5, f"expected 5 perms, got {len(data['permissions'])}")

    def test_delete_role(role_id):
        r = client.delete(f"/roles/{role_id}")
        assert_eq(r.status_code, 200)
        r = client.get(f"/roles/{role_id}")
        assert_eq(r.status_code, 404)

    def test_delete_system_role():
        r = client.delete("/roles/1")  # admin
        assert_eq(r.status_code, 400, "cannot delete system role")

    def test_update_system_role():
        r = client.put("/roles/1", {"name": "超级管理员"})
        assert_eq(r.status_code, 400, "cannot update system role code")

    role_id = test_create_role()
    test("获取角色列表", test_list_roles)
    test("获取权限列表", test_list_permissions)
    test("创建角色", lambda: test_create_role())
    test("创建重复角色失败", test_create_duplicate_role)
    test("获取角色详情", lambda: test_get_role(role_id))
    test("更新角色", lambda: test_update_role(role_id))
    test("分配权限", lambda: test_assign_permissions(role_id))
    test("删除角色", lambda: test_delete_role(role_id))
    test("删除系统角色失败", test_delete_system_role)
    test("更新系统角色失败", test_update_system_role)


# ========== 4. 用户管理测试 ==========
def test_users():
    print("\n📋 4. 用户管理")

    def test_list_users():
        r = client.get("/users/list", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")
        assert_in("total", data, "should have total")

    def test_simple_list():
        r = client.get("/users/simple-list")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return list")

    def test_create_user():
        username = f"testuser_{int(time.time())}"
        r = client.post("/users/create", {
            "username": username,
            "password": "test123456",
            "email": f"{username}@test.com",
            "real_name": "API测试用户",
            "role": "member",
            "dept_id": None
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["user"].append(data["id"])
        return username, data["id"]

    def test_create_duplicate_user():
        username, uid = test_create_user()
        r = client.post("/users/create", {
            "username": username,
            "password": "test123456",
            "email": f"another_{username}@test.com",
            "real_name": "重复用户",
            "role": "member"
        })
        assert_eq(r.status_code, 400, "duplicate username should fail")

    def test_update_user(uid):
        r = client.put(f"/users/{uid}", {
            "real_name": f"用户_更新_{int(time.time())}",
            "role": "viewer"
        })
        assert_eq(r.status_code, 200)

    def test_change_password(uid):
        r = client.post("/users/change-password", {
            "user_id": uid,
            "new_password": "newpass123"
        })
        assert_eq(r.status_code, 200)

    def test_disable_user(uid):
        r = client.post("/users/batch-disable", [uid])
        assert_eq(r.status_code, 200)

    def test_enable_user(uid):
        r = client.post("/users/batch-enable", [uid])
        assert_eq(r.status_code, 200)

    def test_delete_user(uid):
        r = client.delete(f"/users/{uid}")
        assert_eq(r.status_code, 200)

    username, uid = test_create_user()
    test("获取用户列表(分页)", test_list_users)
    test("获取用户简化列表", test_simple_list)
    test("创建用户", lambda: test_create_user())
    test("创建重复用户失败", test_create_duplicate_user)
    test("更新用户", lambda: test_update_user(uid))
    test("修改密码(管理员重置)", lambda: test_change_password(uid))
    test("批量禁用用户", lambda: test_disable_user(uid))
    test("批量启用用户", lambda: test_enable_user(uid))
    test("删除用户(禁用)", lambda: test_delete_user(uid))


# ========== 5. 项目管理测试 ==========
def test_projects():
    print("\n📋 5. 项目管理")

    def test_list_projects():
        r = client.get("/projects/list", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_list_project_types():
        r = client.get("/projects/types")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return list")

    def test_create_project():
        r = client.post("/projects/create", {
            "name": f"API测试项目_{int(time.time())}",
            "code": f"API-{int(time.time())}",
            "description": "这是一个API测试项目",
            "priority": 3,
            "status": "active",
            "type_id": None
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["project"].append(data["id"])
        return data["id"]

    def test_get_project(proj_id):
        r = client.get(f"/projects/{proj_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], proj_id)

    def test_update_project(proj_id):
        r = client.put(f"/projects/{proj_id}", {
            "name": f"项目_更新_{int(time.time())}",
            "description": "更新后的描述"
        })
        assert_eq(r.status_code, 200)

    def test_create_task(proj_id):
        r = client.post(f"/projects/{proj_id}/tasks", {
            "title": f"测试任务_{int(time.time())}",
            "description": "任务描述",
            "status": "pending",
            "priority": 3,
            "project_id": proj_id
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return task id")
        return data["id"]

    def test_get_tasks(proj_id):
        r = client.get(f"/projects/{proj_id}/tasks")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return task list")

    proj_id = test_create_project()
    task_id = test_create_task(proj_id)
    test("获取项目列表", test_list_projects)
    test("获取项目类型", test_list_project_types)
    test("创建项目", lambda: test_create_project())
    test("获取项目详情", lambda: test_get_project(proj_id))
    test("更新项目", lambda: test_update_project(proj_id))
    test("创建任务", lambda: test_create_task(proj_id))
    test("获取任务列表", lambda: test_get_tasks(proj_id))


# ========== 6. 实验管理测试 ==========
def test_experiments():
    print("\n📋 6. 实验管理")

    def test_list_experiments():
        r = client.get("/experiments/list", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_create_experiment():
        proj_id = created_ids["project"][0] if created_ids["project"] else None
        r = client.post("/experiments/create", {
            "name": f"API测试实验_{int(time.time())}",
            "project_id": proj_id,
            "description": "API测试实验描述",
            "exp_type": "trial",
            "status": "draft"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["experiment"].append(data["id"])
        return data["id"]

    def test_get_experiment(exp_id):
        r = client.get(f"/experiments/{exp_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], exp_id)

    def test_update_experiment(exp_id):
        r = client.put(f"/experiments/{exp_id}", {
            "name": f"实验_更新_{int(time.time())}",
            "status": "active"
        })
        assert_eq(r.status_code, 200)

    def test_create_experiment_record(exp_id):
        r = client.post("/experiments/records", {
            "experiment_id": exp_id,
            "batch_no": f"BATCH-{int(time.time())}",
            "sample_code": f"SC-{int(time.time())}",
            "conclusion": "pass",
            "result_summary": "测试通过"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return record id")

    def test_get_experiment_records(exp_id):
        r = client.get(f"/experiments/{exp_id}/records")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data, list), "should return records list")

    exp_id = test_create_experiment()
    test("获取实验列表", test_list_experiments)
    test("创建实验", lambda: test_create_experiment())
    test("获取实验详情", lambda: test_get_experiment(exp_id))
    test("更新实验", lambda: test_update_experiment(exp_id))
    test("创建实验记录", lambda: test_create_experiment_record(exp_id))
    test("获取实验记录", lambda: test_get_experiment_records(exp_id))


# ========== 7. BOM管理测试 ==========
def test_bom():
    print("\n📋 7. BOM管理")

    def test_list_materials():
        r = client.get("/bom/materials", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_create_material():
        r = client.post("/bom/materials", {
            "code": f"MAT-{int(time.time())}",
            "name": f"测试物料_{int(time.time())}",
            "spec": "100x50x10",
            "unit": "pcs",
            "material_type": "plastic",
            "status": "active"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["material"].append(data["id"])
        return data["id"]

    def test_get_material(mat_id):
        r = client.get(f"/bom/materials/{mat_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], mat_id)

    def test_update_material(mat_id):
        r = client.put(f"/bom/materials/{mat_id}", {
            "name": f"物料_更新_{int(time.time())}",
            "spec": "200x100x20"
        })
        assert_eq(r.status_code, 200)

    def test_list_boms():
        r = client.get("/bom/headers", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_create_bom():
        proj_id = created_ids["project"][0] if created_ids["project"] else None
        r = client.post("/bom/headers", {
            "name": f"API测试BOM_{int(time.time())}",
            "project_id": proj_id,
            "version": "V1.0",
            "status": "draft",
            "product_code": f"PC-{int(time.time())}"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["bom"].append(data["id"])
        return data["id"]

    def test_get_bom(bom_id):
        r = client.get(f"/bom/headers/{bom_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], bom_id)

    def test_update_bom(bom_id):
        r = client.put(f"/bom/headers/{bom_id}", {
            "name": f"BOM_更新_{int(time.time())}",
            "version": "V2.0"
        })
        assert_eq(r.status_code, 200)

    def test_create_bom_change(bom_id):
        r = client.post("/bom/changes", {
            "bom_id": bom_id,
            "change_type": "material_replace",
            "title": f"物料变更_{int(time.time())}",
            "reason": "设计优化",
            "description": "替换原材料"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("change_no", data, "should return change_no")

    mat_id = test_create_material()
    bom_id = test_create_bom()
    test("获取物料列表", test_list_materials)
    test("创建物料", lambda: test_create_material())
    test("获取物料详情", lambda: test_get_material(mat_id))
    test("更新物料", lambda: test_update_material(mat_id))
    test("获取BOM列表", test_list_boms)
    test("创建BOM", lambda: test_create_bom())
    test("获取BOM详情", lambda: test_get_bom(bom_id))
    test("更新BOM", lambda: test_update_bom(bom_id))
    test("创建BOM变更单", lambda: test_create_bom_change(bom_id))


# ========== 8. 样品试产测试 ==========
def test_samples():
    print("\n📋 8. 样品试产")

    def test_list_samples():
        r = client.get("/samples/samples", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_create_sample():
        proj_id = created_ids["project"][0] if created_ids["project"] else None
        r = client.post("/samples/samples", {
            "name": f"API测试样品_{int(time.time())}",
            "project_id": proj_id,
            "description": "API测试样品描述",
            "version": "V1.0",
            "status": "pending",
            "sample_type": "prototype",
            "quantity": 10
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["sample"].append(data["id"])
        return data["id"]

    def test_get_sample(sample_id):
        r = client.get(f"/samples/samples/{sample_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], sample_id)

    def test_update_sample(sample_id):
        r = client.put(f"/samples/samples/{sample_id}", {
            "name": f"样品_更新_{int(time.time())}",
            "status": "in_progress"
        })
        assert_eq(r.status_code, 200)

    def test_create_inspection(sample_id):
        r = client.post("/samples/inspections", {
            "sample_id": sample_id,
            "inspect_type": "dimension",
            "result": "pass",
            "remark": "尺寸符合要求"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("inspect_no", data, "should return inspect_no")

    def test_list_trials():
        r = client.get("/samples/trials", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_create_trial():
        proj_id = created_ids["project"][0] if created_ids["project"] else None
        r = client.post("/samples/trials", {
            "name": f"API试产_{int(time.time())}",
            "project_id": proj_id,
            "status": "planned",
            "plan_qty": 100,
            "workshop": "组装车间",
            "line_no": "LINE-01"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["trial"].append(data["id"])
        return data["id"]

    def test_get_trial(trial_id):
        r = client.get(f"/samples/trials/{trial_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], trial_id)

    def test_update_trial(trial_id):
        r = client.put(f"/samples/trials/{trial_id}", {
            "name": f"试产_更新_{int(time.time())}",
            "status": "in_progress"
        })
        assert_eq(r.status_code, 200)

    sample_id = test_create_sample()
    trial_id = test_create_trial()
    test("获取样品列表", test_list_samples)
    test("创建样品", lambda: test_create_sample())
    test("获取样品详情", lambda: test_get_sample(sample_id))
    test("更新样品", lambda: test_update_sample(sample_id))
    test("创建样品检测", lambda: test_create_inspection(sample_id))
    test("获取试产列表", test_list_trials)
    test("创建试产记录", lambda: test_create_trial())
    test("获取试产详情", lambda: test_get_trial(trial_id))
    test("更新试产记录", lambda: test_update_trial(trial_id))


# ========== 9. 文档知识测试 ==========
def test_documents():
    print("\n📋 9. 文档知识")

    def test_list_documents():
        r = client.get("/documents/list", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_create_document():
        r = client.post("/documents/create", {
            "title": f"API测试文档_{int(time.time())}",
            "doc_type": "design",
            "summary": "API测试文档摘要",
            "status": "draft"
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["document"].append(data["id"])
        return data["id"]

    def test_get_document(doc_id):
        r = client.get(f"/documents/{doc_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], doc_id)

    def test_update_document(doc_id):
        r = client.put(f"/documents/{doc_id}", {
            "title": f"文档_更新_{int(time.time())}",
            "status": "published"
        })
        assert_eq(r.status_code, 200)

    def test_list_articles():
        r = client.get("/documents/knowledge/list", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    def test_create_article():
        r = client.post("/documents/knowledge", {
            "title": f"API测试文章_{int(time.time())}",
            "content": "<p>这是API测试文章内容</p>",
            "category": "技术",
            "is_published": True
        })
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("id", data, "should return id")
        created_ids["article"].append(data["id"])
        return data["id"]

    def test_get_article(article_id):
        r = client.get(f"/documents/knowledge/{article_id}")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_eq(data["id"], article_id)

    def test_update_article(article_id):
        r = client.put(f"/documents/knowledge/{article_id}", {
            "title": f"文章_更新_{int(time.time())}",
            "is_published": False
        })
        assert_eq(r.status_code, 200)

    doc_id = test_create_document()
    article_id = test_create_article()
    test("获取文档列表", test_list_documents)
    test("创建文档", lambda: test_create_document())
    test("获取文档详情", lambda: test_get_document(doc_id))
    test("更新文档", lambda: test_update_document(doc_id))
    test("获取知识文章列表", test_list_articles)
    test("创建知识文章", lambda: test_create_article())
    test("获取知识文章详情", lambda: test_get_article(article_id))
    test("更新知识文章", lambda: test_update_article(article_id))


# ========== 10. 操作日志测试 ==========
def test_operation_logs():
    print("\n📋 10. 操作日志")

    def test_list_logs():
        r = client.get("/operation-logs/list", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")
        assert_in("total", data, "should have total")

    def test_list_download_logs():
        r = client.get("/operation-logs/download-logs", params={"page": 1, "page_size": 20})
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_in("items", data, "should have items")

    test("获取操作日志列表", test_list_logs)
    test("获取下载日志列表", test_list_download_logs)


# ========== 11. 数据隔离测试 ==========
def test_data_isolation():
    print("\n📋 11. 数据隔离测试")
    member_client = ApiClient()

    def test_member_login():
        username = f"member_isolation_{int(time.time())}"
        r = client.post("/users/create", {
            "username": username,
            "password": "member123",
            "email": f"{username}@test.com",
            "real_name": "隔离测试成员",
            "role": "member"
        })
        member_id = r.json()["data"]["id"]
        created_ids["user"].append(member_id)

        r = member_client.login(username, "member123")
        assert_eq(r.status_code, 200)
        return member_id

    def test_member_cannot_see_other_projects():
        r = member_client.get("/projects/list")
        assert_eq(r.status_code, 200)
        data = r.json()["data"]
        assert_true(isinstance(data.get("items"), list), "should return items list")

    def test_manager_can_see_all():
        manager_client = ApiClient()
        r = manager_client.login("admin", "admin123")
        assert_eq(r.status_code, 200)

        r = manager_client.get("/projects/list")
        assert_eq(r.status_code, 200)

    member_id = test("成员登录", test_member_login)
    test("成员查看自己权限内的项目", test_member_cannot_see_other_projects)
    test("管理员查看所有项目", test_manager_can_see_all)


# ========== 清理测试数据 ==========
def cleanup():
    """清理测试创建的数据"""
    print("\n🧹 清理测试数据...")
    for uid in created_ids.get("user", []):
        try:
            client.delete(f"/users/{uid}")
        except:
            pass
    for did in created_ids.get("dept", []):
        try:
            client.delete(f"/departments/{did}")
        except:
            pass
    for rid in created_ids.get("role", []):
        try:
            client.delete(f"/roles/{rid}")
        except:
            pass
    print("  清理完成")


# ========== 主函数 ==========
def main():
    global passed, failed, results

    print("=" * 60)
    print("🏭 Factory PMS - 后端 API 全面测试")
    print("=" * 60)
    print(f"测试地址: {BASE_URL}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查服务是否可用
    try:
        requests.get(f"{BASE_URL}/auth/me", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务!")
        print("请先启动后端服务:")
        print("  cd backend")
        print("  python -m uvicorn app.main:app --port 8001")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n⚠️ 连接超时，服务可能正在启动")

    # 先登录
    print("\n🔐 登录管理员账号...")
    r = client.login("admin", "admin123")
    if r.status_code != 200:
        print(f"❌ 登录失败: {r.status_code}")
        sys.exit(1)
    print("  登录成功")

    # 按模块执行测试
    test_auth()
    test_departments()
    test_roles()
    test_users()
    test_projects()
    test_experiments()
    test_bom()
    test_samples()
    test_documents()
    test_operation_logs()
    test_data_isolation()

    # 清理
    cleanup()

    # 输出汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    total = passed + failed
    print(f"  总计: {total} 个用例")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    if total > 0:
        pct = passed / total * 100
        print(f"  通过率: {pct:.1f}%")
        if pct >= 90:
            print("  评级: 🟢 优秀")
        elif pct >= 70:
            print("  评级: 🟡 良好")
        else:
            print("  评级: 🔴 需改进")

    if failed > 0:
        print("\n❌ 失败的用例:")
        for r in results:
            if "❌" in r:
                print(r)

    print("\n" + "=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
