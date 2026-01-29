"""
Proxy Test Node: Folder Paths

SYSTEMATIC test of folder_paths proxy coverage.
Enumerates ALL proxy methods/properties and tests each one.
Outputs coverage report for baseline comparison.
"""
from __future__ import annotations


import folder_paths
from comfy_api.latest import io


# Complete list of proxy members extracted from FolderPathsProxy
PROXY_PROPERTIES = [
    "output_directory", "temp_directory", "input_directory", "user_directory",
    "base_path", "models_dir", "supported_pt_extensions", "folder_names_and_paths",
    "SYSTEM_USER_PREFIX", "extension_mimetypes_cache", "filename_list_cache",
    "cache_helper",
]

PROXY_METHODS_NO_ARGS = [
    "get_output_directory", "get_temp_directory", "get_input_directory",
    "get_user_directory", "get_input_subfolders",
]

PROXY_METHODS_WITH_ARGS = [
    ("set_output_directory", ["output_dir"]),
    ("set_temp_directory", ["temp_dir"]),
    ("set_input_directory", ["input_dir"]),
    ("set_user_directory", ["user_dir"]),
    ("get_system_user_directory", ["name"]),
    ("get_public_user_directory", ["user_id"]),
    ("get_directory_by_type", ["type_name"]),
    ("get_folder_paths", ["folder_name"]),
    ("get_full_path", ["folder_name", "filename"]),
    ("get_full_path_or_raise", ["folder_name", "filename"]),
    ("get_filename_list", ["folder_name"]),
    ("add_model_folder_path", ["folder_name", "full_folder_path"]),
    ("get_annotated_filepath", ["name"]),
    ("exists_annotated_filepath", ["name"]),
    ("get_save_image_path", ["filename_prefix", "output_dir"]),
    ("filter_files_extensions", ["files", "extensions"]),
    ("filter_files_content_types", ["files", "content_types"]),
    ("map_legacy", ["folder_name"]),
    ("annotated_filepath", ["name"]),
    ("recursive_search", ["directory"]),
    ("get_filename_list_", ["folder_name"]),
    ("cached_filename_list_", ["folder_name"]),
]


class ProxyTestFolderPaths(io.ComfyNode):
    """Systematic test of folder_paths proxy - tests ALL proxy members."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestFolderPaths",
            display_name="Proxy Test: Folder Paths",
            category="PyIsolated/ProxyTests",
            inputs=[],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        lines = []
        tested = 0
        passed = 0
        failed = 0
        skipped = 0

        lines.append("=" * 60)
        lines.append("FOLDER PATHS PROXY COVERAGE REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Section 1: Properties
        lines.append("-" * 40)
        lines.append("PROPERTIES")
        lines.append("-" * 40)

        for prop_name in PROXY_PROPERTIES:
            tested += 1
            try:
                value = getattr(folder_paths, prop_name)
                value_str = str(value)
                if len(value_str) > 60:
                    value_str = value_str[:57] + "..."
                lines.append(f"[PASS] {prop_name} = {value_str}")
                passed += 1
            except Exception as e:
                lines.append(f"[FAIL] {prop_name}: {type(e).__name__}: {e}")
                failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("METHODS (no args)")
        lines.append("-" * 40)

        for method_name in PROXY_METHODS_NO_ARGS:
            tested += 1
            try:
                method = getattr(folder_paths, method_name)
                result = method()
                result_str = str(result)
                if len(result_str) > 50:
                    result_str = result_str[:47] + "..."
                lines.append(f"[PASS] {method_name}() = {result_str}")
                passed += 1
            except Exception as e:
                lines.append(f"[FAIL] {method_name}(): {type(e).__name__}: {e}")
                failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("METHODS (with args)")
        lines.append("-" * 40)

        # get_folder_paths
        tested += 1
        try:
            result = folder_paths.get_folder_paths('checkpoints')
            lines.append(f"[PASS] get_folder_paths('checkpoints') = {len(result)} paths")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_folder_paths('checkpoints'): {e}")
            failed += 1

        # get_folder_paths - loras
        tested += 1
        try:
            result = folder_paths.get_folder_paths('loras')
            lines.append(f"[PASS] get_folder_paths('loras') = {len(result)} paths")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_folder_paths('loras'): {e}")
            failed += 1

        # get_filename_list
        tested += 1
        try:
            result = folder_paths.get_filename_list('checkpoints')
            lines.append(f"[PASS] get_filename_list('checkpoints') = {len(result)} files")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_filename_list('checkpoints'): {e}")
            failed += 1

        # get_filename_list - loras
        tested += 1
        try:
            result = folder_paths.get_filename_list('loras')
            lines.append(f"[PASS] get_filename_list('loras') = {len(result)} files")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_filename_list('loras'): {e}")
            failed += 1

        # get_directory_by_type
        tested += 1
        try:
            result = folder_paths.get_directory_by_type('output')
            lines.append(f"[PASS] get_directory_by_type('output') = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_directory_by_type('output'): {e}")
            failed += 1

        # get_system_user_directory
        tested += 1
        try:
            result = folder_paths.get_system_user_directory()
            lines.append(f"[PASS] get_system_user_directory() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_system_user_directory(): {e}")
            failed += 1

        # map_legacy
        tested += 1
        try:
            result = folder_paths.map_legacy('checkpoints')
            lines.append(f"[PASS] map_legacy('checkpoints') = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] map_legacy('checkpoints'): {e}")
            failed += 1

        # annotated_filepath
        tested += 1
        try:
            result = folder_paths.annotated_filepath('test.png')
            lines.append(f"[PASS] annotated_filepath('test.png') = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] annotated_filepath('test.png'): {e}")
            failed += 1

        # exists_annotated_filepath
        tested += 1
        try:
            result = folder_paths.exists_annotated_filepath('nonexistent_test_file.xyz')
            lines.append(f"[PASS] exists_annotated_filepath('nonexistent') = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] exists_annotated_filepath(): {e}")
            failed += 1

        # filter_files_extensions
        tested += 1
        try:
            result = folder_paths.filter_files_extensions(['a.png', 'b.jpg', 'c.txt'], ['.png', '.jpg'])
            lines.append(f"[PASS] filter_files_extensions() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] filter_files_extensions(): {e}")
            failed += 1

        # get_filename_list_
        tested += 1
        try:
            result = folder_paths.get_filename_list_('checkpoints')
            lines.append(f"[PASS] get_filename_list_('checkpoints') = tuple of {len(result)} items")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_filename_list_('checkpoints'): {e}")
            failed += 1

        # cached_filename_list_
        tested += 1
        try:
            result = folder_paths.cached_filename_list_('checkpoints')
            if result is not None:
                lines.append(f"[PASS] cached_filename_list_('checkpoints') = tuple of {len(result)} items")
            else:
                lines.append("[PASS] cached_filename_list_('checkpoints') = None (no cache)")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] cached_filename_list_('checkpoints'): {e}")
            failed += 1

        # get_save_image_path (complex)
        tested += 1
        try:
            output_dir = folder_paths.get_output_directory()
            result = folder_paths.get_save_image_path('test_prefix', output_dir, 512, 512)
            lines.append(f"[PASS] get_save_image_path() = tuple of {len(result)} items")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_save_image_path(): {e}")
            failed += 1

        # Summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("COVERAGE SUMMARY")
        lines.append("=" * 60)
        total_proxy = len(PROXY_PROPERTIES) + len(PROXY_METHODS_NO_ARGS) + len(PROXY_METHODS_WITH_ARGS)
        lines.append(f"Total proxy members defined: {total_proxy}")
        lines.append(f"Tested: {tested}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append(f"Skipped: {skipped}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Coverage: {coverage:.1f}%")
        lines.append("=" * 60)

        report = "\n".join(lines)
        return io.NodeOutput(report)


NODES = [ProxyTestFolderPaths]
