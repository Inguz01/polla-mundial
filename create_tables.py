from database.postgres import engine
from database.models import Base

Base.metadata.create_all(engine)

print("✅ Tablas creadas")