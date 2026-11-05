#!/usr/bin/env python3
"""Real Mach-O fixtures verify that Neo packaging cannot retain Intel helpers."""
from pathlib import Path
import importlib.util,subprocess,tempfile,unittest,shutil
ROOT=Path(__file__).resolve().parents[1]
class PackageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('package_neo',ROOT/'scripts/package-neo.py');cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def fixture(self):
  c=self.root/'hello.c';c.write_text('int main(void){return 0;}\n')
  for arch in ['arm64','x86_64']:subprocess.run(['xcrun','clang','-arch',arch,str(c),'-o',str(self.root/arch)],check=True)
  app=self.root/'Subler Neo.app';main=app/'Contents/MacOS/Neo';main.parent.mkdir(parents=True)
  subprocess.run(['lipo','-create',str(self.root/'arm64'),str(self.root/'x86_64'),'-output',str(main)],check=True)
  nested=app/'Contents/Frameworks/Updater.framework/Versions/A/Updater';nested.parent.mkdir(parents=True);shutil.copy2(main,nested)
  return app,main,nested
 def test_all_embedded_macho_are_thinned(self):
  app,main,nested=self.fixture();original=main.read_bytes();copy=self.root/'prepared.app';shutil.copytree(app,copy)
  entries=self.module.thin_bundle(copy)
  self.assertEqual(len(entries),2)
  for path in [copy/main.relative_to(app),copy/nested.relative_to(app)]:self.assertEqual(subprocess.check_output(['lipo','-archs',str(path)],text=True).split(),['arm64'])
  self.assertEqual(main.read_bytes(),original)
 def test_intel_only_helper_is_rejected(self):
  app,main,nested=self.fixture();shutil.copy2(self.root/'x86_64',nested)
  with self.assertRaisesRegex(RuntimeError,'arm64'):self.module.thin_bundle(app)
 def test_missing_non_system_dylib_is_rejected(self):
  app,main,nested=self.fixture()
  libsource=self.root/'missing.c';libsource.write_text('int missing(void){return 0;}\n')
  library=self.root/'libmissing.dylib'
  subprocess.run(['xcrun','clang','-arch','arm64','-dynamiclib',str(libsource),'-Wl,-install_name,@rpath/libmissing.dylib','-o',str(library)],check=True)
  source=self.root/'consumer.c';source.write_text('extern int missing(void);int main(void){return missing();}\n')
  subprocess.run(['xcrun','clang','-arch','arm64',str(source),str(library),'-o',str(main)],check=True)
  entries=self.module.thin_bundle(app)
  with self.assertRaisesRegex(RuntimeError,'libmissing.dylib'):self.module.validate_dependencies(app,entries)
 def test_non_executable_resources_untouched(self):
  app,main,nested=self.fixture();resource=app/'Contents/icon.png';resource.write_bytes(b'PNG resource fixture')
  self.module.thin_bundle(app);self.assertEqual(resource.read_bytes(),b'PNG resource fixture')
if __name__=='__main__':unittest.main()
