import json
import aiohttp

from aquavalet import streams, provider, exceptions
from aquavalet.providers.utils import require_group, require_match

message_no_internal_provider = "No internal provider in url, path must follow pattern ^\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?"
message_no_resource = "No resource in url, path must follow pattern ^\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?"
message_no_path = "No path in url, path must follow pattern ^\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?"


class OsfProvider(provider.BaseProvider):
    NAME = "OSF"
    PATH_PATTERN = r"^\/(?P<internal_provider>osfstorage)\/(?P<resource>[a-zA-Z0-9]{5,})\/((?P<path>[a-zA-Z0-9]{,}))"

    @property
    def default_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    async def validate_item(self, path):
        match = require_match(self.PATH_PATTERN, path, "match could not be found")
        self.internal_provider = require_group(
            match, "internal_provider", message_no_internal_provider
        )
        self.resource = require_group(match, "resource", message_no_resource)

        if not match.groupdict().get("path"):
            return self.Item.root(self.internal_provider, self.resource)
        else:
            path = require_group(match, "path", message_no_path)
        if self.internal_provider == "osfstorage":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=self.API_URL.format(path=path),
                    headers=self.default_headers,
                ) as resp:
                    if resp.status == 200:
                        data = (await resp.json())["data"]
                    else:
                        raise await self.handle_response(resp, path=path)

        return self.Item(data, self.internal_provider, self.resource)

    async def download(self, item, session, version=None, range=None):
        download_header = self.default_headers

        if range:
            download_header.update({"Range": str(self._build_range_header(range))})

        path = f"{self.resource}/providers/{self.internal_provider}{item.id}"

        if version:
            path += f"?version={version}"

        resp = await session.get(url=self.BASE_URL + path, headers=download_header)
        return streams.http.ResponseStreamReader(resp, range)

    async def upload(self, item, stream, new_name, conflict="warn"):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                data=stream,
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}",
                headers=self.default_headers,
                params={"kind": "file", "name": new_name, "conflict": conflict},
            ) as resp:
                if resp.status in (200, 201):
                    data = (await resp.json())["data"]
                else:
                    return await self.handle_response(
                        resp=resp,
                        item=item,
                        new_name=new_name,
                        stream=stream,
                        conflict=conflict,
                    )

            return self.Item(data, self.internal_provider, self.resource)

    async def handle_conflict_new_version(
        self, resp, item, path, stream, new_name, conflict
    ):
        children = await self.children(item)
        try:
            item = next(item for item in children if item.name == new_name)
        except StopIteration:
            raise exceptions.Gone(f"Item at path '{item.name}' is gone.")

        async with aiohttp.ClientSession() as session:
            async with session.put(
                data=stream,
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}",
                headers=self.default_headers,
            ) as resp:
                if resp.status in (200, 201):
                    data = (await resp.json())["data"]
                else:
                    return await self.handle_response(
                        resp=resp,
                        item=item,
                        new_name=new_name,
                        stream=stream,
                        conflict=conflict,
                    )

            return self.Item(data, self.internal_provider, self.resource)

    async def delete(self, item, confirm_delete=0):
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}",
                params={"confirm_delete": 0},
                headers=self.default_headers,
            ) as resp:
                if resp.status in (204,):
                    return None
                else:
                    raise await self.handle_response(resp, item)

    async def metadata(self, item, version=None):
        return item

    async def create_folder(self, item, new_name):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}",
                headers=self.default_headers,
                params={"kind": "folder", "name": new_name},
            ) as resp:
                if resp.status in (201,):
                    data = (await resp.json())["data"]
                else:
                    raise await self.handle_response(resp, item, new_name=new_name)

                return self.Item(data, self.internal_provider, self.resource)

    async def rename(self, item, new_name):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}",
                data=json.dumps({"action": "rename", "rename": new_name}),
                headers=self.default_headers,
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())["data"]
                else:
                    raise await self.handle_response(resp, item)

                return self.Item(data, self.internal_provider, self.resource)

    async def children(self, item):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}",
                headers=self.default_headers,
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())["data"]
                else:
                    raise await self.handle_response(resp, item)

        return self.Item.list(item, data)

    def can_intra_copy(self, dest_provider, item=None):
        if type(self) == type(dest_provider):
            return True

    async def intra_copy(self, item, dest_item, dest_provider=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}",
                data=json.dumps(
                    {
                        "action": "copy",
                        "path": dest_item.path + "/",
                        "provider": "osfstorage",
                        "resource": dest_provider.resource,
                    }
                ),
                headers=self.default_headers,
            ) as resp:
                print(resp)

    async def versions(self, item):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.BASE_URL
                + f"{self.resource}/providers/{self.internal_provider}{item.id}?versions=",
                headers=self.default_headers,
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())["data"]
                else:
                    raise await self.handle_response(resp, item)

        return self.Item.versions(item, data)
