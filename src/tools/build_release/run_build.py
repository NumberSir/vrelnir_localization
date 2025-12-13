"""
运行前提：
1. 写好了 README
2. 写好了 CREDITS
3. 按照 degrees-of-lewdity-master/devTools/apkbuilder/README-windows.txt 配好了 nodejs 和 jdk17

运行步骤：
1. 触发 ModLoader 自动构建
2. 触发汉化包自动构建

3. 下载构建好的 ModLoader 包和图片包
4. 下载构建好的汉化包

5. 解压 ModLoader 包出两个 HTML 文件
6. 把 README, Credits, LICENSE 和 HTML 打成压缩包
7. 替换官方 APK 中的 HTML
8. 删除官方 APK 中的 img 文件夹
9. 计算 MD5
10. 提取出 README 中的本次更新部分
11. 构建 Release
"""
import asyncio
import hashlib
import os
import re
import shutil
import subprocess
import time
import zipfile
from zipfile import ZipFile
from pathlib import Path

import httpx

from github import Github, Auth
from github.Repository import Repository

from src.tools.build_release.download import *
from src.tools.build_release.log import *
from src.tools.build_release.consts import *


class ReleaseBuild:
	def __init__(self, github: Github, client: httpx.AsyncClient):
		self._client = client
		self._github = github
		self._repository: "Repository" = github.get_repo("Eltirosto/Degrees-of-Lewdity-Chinese-Localization")

	""" INIT """
	@staticmethod
	def clear():
		"""清理临时文件夹和构建文件"""
		shutil.rmtree(DIR_TEMP, ignore_errors=True)
		shutil.rmtree(DIR_BUILD_ASSETS, ignore_errors=True)
		os.makedirs(DIR_TEMP, exist_ok=True)
		os.makedirs(DIR_BUILD_ASSETS, exist_ok=True)
		logger.info("initialize successfully")

	""" ACTION """  # TODO
	def _trigger(self):
		"""触发自动构建"""
		...

	def trigger_mod_loader(self):
		"""触发 ModLoader 自动构建 (Lyoko-Jeremie/DoLModLoaderBuild)"""
		...

	def trigger_i18n(self):
		"""触发 I18N 自动构建 (NumberSir/DoL-I18n-Build)"""
		...

	""" DOWNLOAD """
	async def _download(self, repo_name: str):
		"""下载构建好的文件"""
		repo = self.github.get_repo(repo_name)
		release = repo.get_latest_release()
		assets = release.get_assets()
		for asset in assets:
			response = await self.client.head(asset.browser_download_url, timeout=60, follow_redirects=True)
			filesize = int(response.headers["Content-Length"])
			chunks = await chunk_split(filesize, 64)

			if (DIR_TEMP / asset.name).exists():
				continue

			tasks = {
				chunk_download(asset.browser_download_url, self.client, start, end, DIR_TEMP / asset.name)
				for start, end in chunks
			}
			await asyncio.gather(*tasks)

	async def download_mod_loader(self):
		"""下载 ModLoader 和 Imagepack"""
		await self._download("Lyoko-Jeremie/DoLModLoaderBuild")
		logger.info("ModLoader & Imagepack downloaded successfully")

	async def download_i18n(self):
		"""下载 ModI18N """
		await self._download("NumberSir/DoL-I18n-Build")
		logger.info("ModI18N downloaded successfully")

	""" DECOMPRESS """
	def decompress_mod_loader(self):
		"""只要解压出来的 html 文件"""
		with zipfile.ZipFile(DIR_TEMP / self.mod_loader_filename, "r") as zfp:
			for file in zfp.filelist:
				if not file.filename.endswith(".html"):
					continue
				zfp.extract(file, DIR_TEMP)

	""" BUILD ASSETS """
	def move_i18n(self):
		"""统一移到一个文件夹里"""
		shutil.copyfile(
			DIR_TEMP / self.i18n_filename,
			DIR_BUILD_ASSETS / self.i18n_filename,
		)
		logger.info("ModI18N built successfully")

	def rename_image_pack(self):
		"""默认不带版本号，加上"""
		(DIR_TEMP / self.image_pack_filename).rename(DIR_TEMP / f'{self.image_pack_filename.split("-")[0].split(".")[0]}-{self.game_version}.mod.zip')

	def move_image_pack(self):
		"""统一移到一个文件夹里"""
		shutil.copyfile(
			DIR_TEMP / self.image_pack_filename,
			DIR_BUILD_ASSETS / self.image_pack_filename,
		)
		logger.info("Imagepack built successfully")

	def _build_compress(self, html_filepath: Path, polyfill_suffix: str = ""):
		"""构建游戏本体压缩包"""
		with ZipFile(DIR_BUILD_ASSETS / f"DoL-ModLoader-{self.game_version}-v{self.mod_loader_version}{polyfill_suffix}.zip", mode="w", compression=zipfile.ZIP_DEFLATED) as zfp:
			zfp.write(filename=FILE_README, arcname=FILE_README.name, compresslevel=9)
			zfp.write(filename=FILE_LICENSE, arcname=FILE_LICENSE.name, compresslevel=9)
			zfp.write(filename=FILE_CREDITS, arcname=FILE_CREDITS.name, compresslevel=9)
			zfp.write(filename=html_filepath, arcname=HTML_FILENAME, compresslevel=9)
		logger.info(f"Zipfile{polyfill_suffix} built successfully")

	def build_compress_normal(self):
		"""构建游戏本体压缩包 (正常版)"""
		return self._build_compress(DIR_TEMP / self.html_filename)

	def build_compress_polyfill(self):
		"""构建游戏本体压缩包 (兼容版)"""
		return self._build_compress(DIR_TEMP / self.html_polyfill_filename, "-polyfill")

	@staticmethod
	def _pre_build_apk():
		"""用源码自带的打包工具打包前处理环境和打包脚本"""
		with ZipFile(FILE_GRADLE, "r") as zfp:
			zfp.extractall(DIR_APK_BUILDER / "androidsdk" / "gradle")

		with ZipFile(FILE_CMDLINE, "r") as zfp:
			zfp.extractall(DIR_APK_BUILDER / "androidsdk" / "cmdline-tools" / "latest")

		ReleaseBuild._replace_special_texts(DIR_APK_BUILDER / "setup_deps.bat", "pause")
		ReleaseBuild._replace_special_texts(DIR_APK_BUILDER / "build_app_debug.bat", "pause")
		ReleaseBuild._replace_special_texts(DIR_APK_BUILDER / "build_app_release.bat", 'pause')
		ReleaseBuild._replace_special_texts(DIR_APK_BUILDER / "scripts" / "prepare_files.js", '["img"]', "[]")
		ReleaseBuild._replace_special_texts(DIR_APK_BUILDER / "scripts" / "prevent_unnecessary_deletes.js", '["img"]', "[]")
		ReleaseBuild._replace_special_texts(DIR_APK_BUILDER / "www" / "custom_cordova_additions.js", "Press BACK again to exit", "再次点击返回键退出")

	def _build_apk(self, html_filepath: Path, polyfill_suffix: str = ""):
		"""构建游戏本体 apk"""
		self._pre_build_apk()
		shutil.copyfile(
			html_filepath,
			DIR_GAME / HTML_FILENAME,
		)
		subprocess.Popen(DIR_APK_BUILDER / "setup_deps.bat", cwd=DIR_APK_BUILDER).wait()

		if (ROOT / CORDOVA_ANDROID_KEYSTORE_FILENAME).exists():
			shutil.copyfile(ROOT / CORDOVA_ANDROID_KEYSTORE_FILENAME, DIR_GAME / CORDOVA_ANDROID_KEYSTORE_FILENAME)
			self._replace_special_texts(DIR_APK_BUILDER / "scripts" / "build_app.js", "path.resolve(gameRoot, 'keys/dol.keystore');", f"path.resolve(gameRoot, '{CORDOVA_ANDROID_KEYSTORE_FILENAME}');")
			self._replace_special_texts(DIR_APK_BUILDER / "scripts" / "build_app.js", 'alias: "dol"', f'alias: "{CORDOVA_ANDROID_KEYSTORE_ALIAS}"')
			self._replace_special_texts(DIR_APK_BUILDER / "scripts" / "build_app.js", 'let password = ""', f'let password = "{CORDOVA_ANDROID_KEYSTORE_PASSWORD}"/*')
			self._replace_special_texts(DIR_APK_BUILDER / "scripts" / "build_app.js", 'if (password)', '*/ if  (password)')

			subprocess.Popen(DIR_APK_BUILDER / "build_app_release.bat", cwd=DIR_APK_BUILDER, stdout=subprocess.DEVNULL).wait()
			logger.info(f"Apk{polyfill_suffix} CHS built successfully")
		else:
			subprocess.Popen(DIR_APK_BUILDER / "build_app_debug.bat", cwd=DIR_APK_BUILDER, stdout=subprocess.DEVNULL).wait()
			logger.info(f"Apk{polyfill_suffix} DEBUG built successfully")
		shutil.copyfile(
			DIR_DIST / self.apk_filename,
			DIR_BUILD_ASSETS / f"DoL-ModLoader-{self.game_version}-v{self.mod_loader_version}{polyfill_suffix}.APK",
		)

	def build_apk_normal(self):
		"""构建游戏本体 apk (普通版)"""
		return self._build_apk(DIR_TEMP / self.html_filename)

	def build_apk_polyfill(self):
		"""构建游戏本体 apk (兼容版)"""
		return self._build_apk(DIR_TEMP / self.html_polyfill_filename, "-polyfill")

	@staticmethod
	def rename_pre(flag: bool = True):
		"""如果是预发布，就加上 pre 后缀"""
		if not flag:
			return
		for file in os.listdir(DIR_BUILD_ASSETS):
			if file.endswith(".mod.zip"):
				shutil.move(DIR_BUILD_ASSETS / file, DIR_BUILD_ASSETS / f"{file[:-8]}-pre{file[-8:]}".replace("-pre-pre", "-pre"))
			else:
				shutil.move(DIR_BUILD_ASSETS / file, DIR_BUILD_ASSETS / f"{file[:-4]}-pre{file[-4:]}".replace("-pre-pre", "-pre"))

	""" BUILD RELEASE """
	@staticmethod
	def fetch_changelog() -> str:
		"""手动填好 README 之后提取本次的更新日志"""
		with open(FILE_README, "r", encoding="utf-8") as fp:
			lines = fp.readlines()

		result = ""
		issues = []
		flag = False
		for line in lines:
			line = line.strip(">").strip().strip("-").strip()
			if not line:
				continue

			if not line.startswith("20") and not flag:
				continue

			if flag:
				if line.startswith("20"):
					break
				result = f"{result}\n{line}"
			flag = True

		issues.extend(re.findall(r"\[(issue[\-dc]*\d+)*?]", result))
		result = f"{result}\n"
		for line in lines:
			if not line.startswith("[issue"):
				continue

			issue = line.split(":")[0].strip("[").strip("]")
			if issue not in issues:
				continue

			result = f"{result}\n{line.strip()}"
		return result

	@staticmethod
	def calculate_md5() -> str:
		"""计算上传文件的 MD5 值"""
		result = "md5:"
		for file in os.listdir(DIR_BUILD_ASSETS):
			with open(DIR_BUILD_ASSETS / file, "rb") as fp:
				content = fp.read()
			result = f"{result}\n`{file}`: `{hashlib.md5(content).hexdigest()}`"
		return result

	@property
	def section_changelog(self) -> str:
		"""最终发布日志中的更新日志部分"""
		return self.fetch_changelog()

	@property
	def section_md5(self) -> str:
		"""最终发布日志中的 MD5 部分"""
		return self.calculate_md5()

	def generate_release_note(self) -> str:
		"""生成最终的发布日志"""
		return (
			f"{self.section_changelog}"
			"\n\n"
			f"{self.section_md5}"
			"\n\n"
			"## 致谢名单\n"
			"[CREDITS.md](CREDITS.md)"
		)

	def save_release_note(self):
		"""保存到本地以便校对"""
		with open(DIR_BUILD / "note.md", "w", encoding="utf-8") as fp:
			fp.write(self.release_note)
		logger.info("release note generated successfully")

	def release(self, *, draft: bool = True):
		"""
		发布！

		:param draft: 是否是草稿
		"""
		git_release = self.repository.create_git_release(
			tag=f"v{self.game_version}-chs-{self.i18n_version}",
			name=f"v{self.game_version}-chs-{self.i18n_version}",
			message=self.release_note,
			draft=draft
		)
		for file in os.listdir(DIR_BUILD_ASSETS):
			git_release.upload_asset(
				path=(DIR_BUILD_ASSETS / file).__str__()
			)
		logger.info(f"RELEASE{'-draft' if draft else ''} successfully")

	""" PROPERTY """
	@property
	def client(self) -> httpx.AsyncClient:
		"""http 客户端"""
		return self._client

	@property
	def github(self) -> Github:
		"""github 客户端"""
		return self._github

	@property
	def repository(self) -> Repository:
		"""发布仓库"""
		return self._repository

	@property
	def release_note(self) -> str:
		"""发布日志"""
		return self.generate_release_note()

	""" FILENAME """
	@staticmethod
	def _get_tmp_filename(prefix: str = "", suffix: str = "") -> str:
		"""下载的 artifact 的文件名"""
		return [
			file
			for file in os.listdir(DIR_TEMP)
			if file.startswith(prefix)
			if file.endswith(suffix)
		][0]

	@staticmethod
	def _get_dist_filename() -> str:
		"""构建好的 apk 的文件名"""
		return list(os.listdir(DIR_GAME / "dist"))[0]

	@staticmethod
	def _replace_special_texts(filepath: Path, old: str, new: str = ""):
		with open(filepath, "r", encoding="utf-8") as fp:
			content = fp.read()
		with open(filepath, "w", encoding="utf-8") as fp:
			fp.write(content.replace(old, new))

	def get_mod_loader_filename(self) -> str:
		"""下载的自动构建的 modloader 的文件名"""
		return self._get_tmp_filename(prefix="DoL-ModLoader")

	def get_image_pack_filename(self) -> str:
		"""下载的自动构建的 imagepack 的文件名"""
		return self._get_tmp_filename(prefix="GameOriginalImagePack")

	def get_i18n_filename(self) -> str:
		"""下载的自动构建的 i18n 的文件名"""
		return self._get_tmp_filename(prefix="ModI18N")

	def get_html_filename(self) -> str:
		"""解压出来的普通游戏本体 html 文件名"""
		return self._get_tmp_filename(prefix="Degrees of Lewdity", suffix="mod.html")

	def get_html_polyfill_filename(self) -> str:
		"""解压出来的兼容游戏本体 html 文件名"""
		return self._get_tmp_filename(prefix="Degrees of Lewdity", suffix="polyfill.html")

	@property
	def mod_loader_filename(self) -> str:
		"""下载的自动构建的 modloader 的文件名"""
		return self.get_mod_loader_filename()

	@property
	def image_pack_filename(self) -> str:
		"""下载的自动构建的 imagepack 的文件名"""
		return self.get_image_pack_filename()

	@property
	def i18n_filename(self) -> str:
		"""下载的自动构建的 i18n 的文件名"""
		return self.get_i18n_filename()

	@property
	def html_filename(self) -> str:
		"""解压出来的普通游戏本体 html 文件名"""
		return self.get_html_filename()

	@property
	def html_polyfill_filename(self) -> str:
		"""解压出来的兼容游戏本体 html 文件名"""
		return self.get_html_polyfill_filename()

	@property
	def apk_filename(self) -> str:
		"""构建好的 apk 的文件名"""
		return self._get_dist_filename()

	""" VERSION """
	@staticmethod
	def get_game_version() -> str:
		"""游戏本体版本号"""
		with open(DIR_GAME / "version", "r", encoding="utf-8") as fp:
			return fp.read().strip()

	def get_i18n_version(self) -> str:
		"""i18n 版本号"""
		return self.i18n_filename.rstrip('mod.zip').split("-")[-1]

	def get_mod_loader_version(self) -> str:
		"""modloader 版本号"""
		return self.mod_loader_filename.split("-")[2]

	@property
	def game_version(self) -> str:
		"""游戏本体版本号"""
		return self.get_game_version()

	@property
	def i18n_version(self) -> str:
		"""i18n 版本号"""
		return self.get_i18n_version()

	@property
	def mod_loader_version(self) -> str:
		"""游戏本体版本号"""
		return self.get_mod_loader_version()


async def main():
	start = time.time()
	async with httpx.AsyncClient(verify=False) as client:
		with Github(auth=Auth.Token(ACCESS_TOKEN)) as github:
			process = ReleaseBuild(github, client)
			""" 开始 """
			process.clear()

			""" 运行 """  # TODO
			# process.trigger_mod_loader()
			# process.trigger_i18n()

			""" 下载 """
			await process.download_mod_loader()
			await process.download_i18n()

			""" 解压 """
			process.decompress_mod_loader()

			""" 打包 """
			process.rename_image_pack()
			process.move_i18n()
			process.move_image_pack()
			process.build_compress_normal()
			process.build_compress_polyfill()
			process.build_apk_normal()
			process.build_apk_polyfill()
			process.rename_pre(flag=False)  # 预览版

			""" 发布 """  # TODO
			process.release(draft=True)

	cost = time.time() - start
	logger.info(f"cost {cost:.2f} seconds")
	return cost

if __name__ == '__main__':
	cost = asyncio.run(main())

	try:
		from win10toast import ToastNotifier
	except ImportError:
		pass
	else:
		ToastNotifier().show_toast(title="RELEASE SCRIPT RUN DONE", msg=f"cost {cost or -1:.2f}s")

