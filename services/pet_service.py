from routers.datamodels.desk_datamodels import PetResponse
from repositorys.pet_repository import PetRepository


class PetService:
    def __init__(self):
        self.pet_repository = PetRepository()

    def regist(self, conn, oid, pets):
        result = []
        for pet in pets:
            pid = self.pet_repository.insert(conn, oid, pet)
            result.append(PetResponse(pid=pid, **pet.model_dump()))
        return result

    async def get(self, pid, branch):
        pet = await self.pet_repository.find(pid, branch)
        return PetResponse(**pet) if pet else None

    async def find_by_owner(self, oid):
        return [PetResponse(**pet) for pet in await self.pet_repository.find_by_owner(oid)]

    async def find_by_owners(self, oids):
        # {보호자 id: [동물, ...]}
        pets = {oid: [] for oid in oids}
        for pet in await self.pet_repository.find_by_owners(oids):
            pets[pet["oid"]].append(PetResponse(**pet))
        return pets

    async def update(self, pid, data):
        fields = data.model_dump(exclude_unset=True)
        if fields:
            await self.pet_repository.update(pid, fields)
