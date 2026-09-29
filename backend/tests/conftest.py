import os
import tempfile

# Point the app at a throwaway database and storage before app modules are imported,
# so test runs never write into the real legal_saas.db, storage/ or learning/uploads/.
_TEST_ROOT = tempfile.mkdtemp(prefix="legal_saas_tests_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TEST_ROOT, 'test.db')}"
os.environ["STORAGE_DIR"] = os.path.join(_TEST_ROOT, "storage")
os.environ["LEARNING_UPLOADS_DIR"] = os.path.join(_TEST_ROOT, "learning_uploads")
