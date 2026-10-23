from routers.datamodels.desk_datamodels import PetResponse
from routers.datamodels.vet_datamodels import ConsultationResponse, ConsultationDetail
from repositorys.consultation_repository import ConsultationRepository


class ConsultationService:
    def __init__(self):
        self.consultation_repository = ConsultationRepository()

    async def regist(self, pid, data):
        cid = await self.consultation_repository.insert(pid, data.vet_uid, data.purpose)
        return ConsultationResponse(**await self.consultation_repository.find(cid))

    async def history(self, pid, branch):
        return [ConsultationResponse(**row) for row in await self.consultation_repository.find_by_pet(pid, branch)]

    async def active_pids(self, pids):
        return await self.consultation_repository.find_active_pids(pids)

    async def assigned(self, vet_uid):
        return [ConsultationResponse(**row) for row in await self.consultation_repository.find_assigned(vet_uid)]

    async def detail(self, cid, vet_uid):
        row = await self.consultation_repository.find(cid)
        if row is None or row["vet_uid"] != vet_uid:
            return None
        return ConsultationDetail(**row, pet=PetResponse(**row))

    async def change_status(self, cid, vet_uid, before, after):
        if await self.consultation_repository.update_status(cid, vet_uid, before, after) == 0:
            return None
        return await self.detail(cid, vet_uid)

    async def diagnose(self, cid, vet_uid, diagnosis):
        if await self.consultation_repository.update_diagnosis(cid, vet_uid, diagnosis) == 0:
            return None
        return await self.detail(cid, vet_uid)
