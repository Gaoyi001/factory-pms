"""文档管理模块测试"""
import pytest
import time


class TestDocumentCRUD:
    """文档增删改查测试"""

    def test_list_documents(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/documents/list", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_create_document(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/documents/create", json={
            "title": f"测试文档_{int(time.time())}",
            "doc_type": "test",
            "status": "draft",
            "summary": "文档摘要",
            "tags": ["测试", "文档"],
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_get_document(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/documents/create", json={
            "title": f"查询文档_{int(time.time())}",
            "doc_type": "test",
            "status": "active",
        }, headers=headers)
        doc_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == doc_id

    def test_update_document(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/documents/create", json={
            "title": f"更新文档_{int(time.time())}",
            "doc_type": "test",
            "status": "draft",
        }, headers=headers)
        doc_id = create_resp.json()["data"]["id"]

        response = client.put(f"/api/v1/documents/{doc_id}", json={
            "title": f"更新后的标题_{int(time.time())}",
            "status": "released",
        }, headers=headers)
        assert response.status_code == 200

    def test_delete_document(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/documents/create", json={
            "title": f"删除文档_{int(time.time())}",
            "doc_type": "test",
            "status": "draft",
        }, headers=headers)
        doc_id = create_resp.json()["data"]["id"]

        response = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
        assert response.status_code == 200


class TestDocumentVersioning:
    """文档版本管理测试"""

    def test_list_versions(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_resp = client.post("/api/v1/documents/create", json={
            "title": f"版本列表文档_{int(time.time())}",
            "doc_type": "test",
            "status": "active",
        }, headers=headers)
        doc_id = create_resp.json()["data"]["id"]

        response = client.get(f"/api/v1/documents/{doc_id}/versions", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "versions" in data


class TestDocumentKnowledge:
    """文档知识库测试"""

    def test_get_knowledge_list(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/documents/knowledge/list", params={"page": 1, "page_size": 20}, headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data


class TestDocumentValidation:
    """文档参数校验测试"""

    def test_create_document_validation(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.post("/api/v1/documents/create", json={
            "doc_type": "test",
        }, headers=headers)
        assert response.status_code == 422