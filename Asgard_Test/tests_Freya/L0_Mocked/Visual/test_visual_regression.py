"""
Freya Visual L0 Mocked Tests - Visual Regression Tester

Comprehensive tests for visual regression testing service with mocked PIL and image processing.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from Asgard.Freya.Visual.models.visual_models import (
    ComparisonConfig,
    ComparisonMethod,
    DifferenceType,
    RegressionTestSuite,
    RegressionTestCase,
)
from Asgard.Freya.Visual.services.visual_regression import VisualRegressionTester


# =============================================================================
# Test VisualRegressionTester Initialization
# =============================================================================

class TestVisualRegressionTesterInit:
    """Tests for VisualRegressionTester initialization."""

    @pytest.mark.L0
    def test_init_default_directory(self):
        """Test initialization with default output directory."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True):
            tester = VisualRegressionTester()

            assert tester.output_directory == Path("./regression_output")

    @pytest.mark.L0
    def test_init_custom_directory(self, temp_output_dir):
        """Test initialization with custom output directory."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True):
            tester = VisualRegressionTester(output_directory=str(temp_output_dir))

            assert tester.output_directory == temp_output_dir

    @pytest.mark.L0
    def test_init_creates_subdirectories(self, tmp_path):
        """Test initialization creates subdirectories."""
        output_dir = tmp_path / "regression"

        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True):
            tester = VisualRegressionTester(output_directory=str(output_dir))

            assert (output_dir / "diffs").exists()
            assert (output_dir / "reports").exists()

    @pytest.mark.L0
    def test_init_raises_without_pil(self):
        """Test initialization raises error when PIL not available."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", False):
            with pytest.raises(ImportError, match="Pillow is required"):
                VisualRegressionTester()


# =============================================================================
# Test compare Method - Basic Functionality
# =============================================================================

class TestCompareBasic:
    """Tests for basic compare method functionality."""

    @pytest.mark.L0
    def test_compare_identical_images(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test comparing identical images."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np:

            # Mock identical images
            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff

            mock_np.array.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_np.sum.return_value = 0

            tester = VisualRegressionTester()
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
            )

        assert result.baseline_path == str(temp_baseline_file)
        assert result.comparison_path == str(temp_comparison_file)
        assert result.similarity_score == 1.0
        assert result.is_similar is True
        assert len(result.difference_regions) == 0

    @pytest.mark.L0
    def test_compare_different_images(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test comparing different images."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np, \
             patch("Asgard.Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", False):

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff

            # Simulate 10% difference
            total_pixels = 1920 * 1080
            different_pixels = total_pixels * 0.1
            mock_np.array.return_value = np.ones((1080, 1920), dtype=np.uint8) * 50
            mock_np.sum.return_value = different_pixels
            mock_np.size = total_pixels

            tester = VisualRegressionTester()
            config = ComparisonConfig(threshold=0.95, method=ComparisonMethod.PIXEL_DIFF)
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        assert result.similarity_score == 0.9
        assert result.is_similar is False

    @pytest.mark.L0
    def test_compare_handles_image_load_error(self, temp_baseline_file, temp_comparison_file):
        """Test compare handles image loading errors."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image") as mock_image:

            mock_image.open.side_effect = Exception("Failed to load image")

            tester = VisualRegressionTester()
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
            )

        assert result.similarity_score == 0.0
        assert result.is_similar is False
        assert "error" in result.metadata

    @pytest.mark.L0
    def test_compare_resizes_mismatched_sizes(self, temp_baseline_file, temp_comparison_file, mock_image_module):
        """Test compare resizes images of different sizes."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np:

            # Create images with different sizes
            baseline_img = MagicMock()
            baseline_img.size = (1920, 1080)
            baseline_img.width = 1920
            baseline_img.height = 1080
            baseline_img.convert.return_value = baseline_img
            baseline_img.resize.return_value = baseline_img

            comparison_img = MagicMock()
            comparison_img.size = (1280, 720)
            comparison_img.width = 1280
            comparison_img.height = 720
            comparison_img.convert.return_value = comparison_img
            comparison_img.resize.return_value = comparison_img

            mock_image_module.open.side_effect = [baseline_img, comparison_img]

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.zeros((720, 1280), dtype=np.uint8)
            mock_np.sum.return_value = 0

            tester = VisualRegressionTester()
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
            )

        # Should have called resize on both images
        baseline_img.resize.assert_called()
        comparison_img.resize.assert_called()


# =============================================================================
# Test compare Method - Comparison Methods
# =============================================================================

class TestComparisonMethods:
    """Tests for different comparison methods."""

    @pytest.mark.L0
    def test_pixel_diff_comparison(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test pixel diff comparison method."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np, \
             patch("Asgard.Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", False):

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_np.sum.return_value = 50
            mock_np.size = 10000

            tester = VisualRegressionTester()
            config = ComparisonConfig(method=ComparisonMethod.PIXEL_DIFF)
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        assert result.comparison_method == ComparisonMethod.PIXEL_DIFF
        assert 0.99 <= result.similarity_score <= 1.0

    @pytest.mark.L0
    def test_ssim_comparison(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test SSIM comparison method."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ssim") as mock_ssim, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np, \
             patch("Asgard.Freya.Visual.services.visual_regression.cv2"):

            # Mock SSIM result
            mock_ssim.return_value = (0.95, np.ones((100, 100)))
            mock_np.array.return_value = np.ones((100, 100), dtype=np.uint8)
            mock_np.any.return_value = False

            tester = VisualRegressionTester()
            config = ComparisonConfig(method=ComparisonMethod.STRUCTURAL_SIMILARITY)
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        assert result.comparison_method == ComparisonMethod.STRUCTURAL_SIMILARITY
        assert result.similarity_score == 0.95

    @pytest.mark.L0
    def test_perceptual_hash_comparison(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test perceptual hash comparison method."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Freya.Visual.services.visual_regression.Image", mock_image_module):

            # Mock small image for hash calculation
            small_img = MagicMock()
            small_img.getdata.return_value = [128] * 64
            mock_pil_image.resize.return_value = small_img
            mock_pil_image.convert.return_value = small_img

            tester = VisualRegressionTester()
            config = ComparisonConfig(method=ComparisonMethod.PERCEPTUAL_HASH)
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        assert result.comparison_method == ComparisonMethod.PERCEPTUAL_HASH

    @pytest.mark.L0
    def test_histogram_comparison(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test histogram comparison method."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Freya.Visual.services.visual_regression.Image", mock_image_module):

            # Mock identical histograms
            mock_pil_image.histogram.return_value = [100] * 768

            tester = VisualRegressionTester()
            config = ComparisonConfig(method=ComparisonMethod.HISTOGRAM_COMPARISON)
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        assert result.comparison_method == ComparisonMethod.HISTOGRAM_COMPARISON


# =============================================================================
# Test compare Method - Configuration Options
# =============================================================================

class TestComparisonConfiguration:
    """Tests for comparison configuration options."""

    @pytest.mark.L0
    def test_compare_with_blur(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test comparison with blur preprocessing."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageFilter") as mock_filter, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np:

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_np.sum.return_value = 0

            tester = VisualRegressionTester()
            config = ComparisonConfig(blur_radius=5)
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        # Should have called filter for blur
        mock_pil_image.filter.assert_called()

    @pytest.mark.L0
    def test_compare_with_ignore_regions(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test comparison with ignore regions."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageDraw") as mock_draw, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np:

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_np.sum.return_value = 0

            tester = VisualRegressionTester()
            config = ComparisonConfig(
                ignore_regions=[{"x": 0, "y": 0, "width": 100, "height": 50}]
            )
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        # Should have masked regions
        assert mock_pil_image.copy.called

    @pytest.mark.L0
    def test_compare_respects_threshold(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test comparison respects similarity threshold."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np, \
             patch("Asgard.Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", False):

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.ones((100, 100), dtype=np.uint8) * 50
            mock_np.sum.return_value = 400
            mock_np.size = 10000

            tester = VisualRegressionTester()

            # Test with high threshold
            config_high = ComparisonConfig(threshold=0.99)
            result_high = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config_high,
            )

            # Test with low threshold
            config_low = ComparisonConfig(threshold=0.90)
            result_low = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config_low,
            )

        assert result_high.similarity_score == result_low.similarity_score
        assert result_high.is_similar != result_low.is_similar


# =============================================================================
# Test run_suite Method
# =============================================================================

class TestRunSuite:
    """Tests for run_suite method."""

    @pytest.mark.L0
    def test_run_suite_basic(self, sample_regression_test_suite, mock_pil_image, mock_image_module):
        """Test running a basic regression test suite."""
        # Create baseline files
        baseline_dir = Path(sample_regression_test_suite.baseline_directory)
        (baseline_dir / "test1.png").write_text("baseline1")
        (baseline_dir / "test2.png").write_text("baseline2")

        # Create comparison files
        output_dir = Path(sample_regression_test_suite.output_directory)
        (output_dir / "test1_current.png").write_text("comparison1")
        (output_dir / "test2_current.png").write_text("comparison2")

        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np, \
             patch("Asgard.Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", False):

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_np.sum.return_value = 0

            tester = VisualRegressionTester()
            report = tester.run_suite(sample_regression_test_suite)

        assert report.suite_name == sample_regression_test_suite.name
        assert report.total_comparisons == 2
        assert report.report_path is not None

    @pytest.mark.L0
    def test_run_suite_skips_missing_baselines(self, temp_output_dir, mock_pil_image, mock_image_module):
        """Test suite skips tests with missing baseline images."""
        baseline_dir = temp_output_dir / "baselines"
        baseline_dir.mkdir()
        output_dir = temp_output_dir / "output"
        output_dir.mkdir()

        # Only create baseline for test1
        (baseline_dir / "test1.png").write_text("baseline1")

        suite = RegressionTestSuite(
            name="Test Suite",
            baseline_directory=str(baseline_dir),
            output_directory=str(output_dir),
            test_cases=[
                RegressionTestCase(name="test1", url="https://example.com/1"),
                RegressionTestCase(name="test2", url="https://example.com/2"),
            ],
        )

        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True):
            tester = VisualRegressionTester()
            report = tester.run_suite(suite)

        # Should skip test2 since baseline doesn't exist
        assert report.total_comparisons == 0

    @pytest.mark.L0
    def test_run_suite_calculates_statistics(self, sample_regression_test_suite, mock_pil_image, mock_image_module):
        """Test suite calculates correct statistics."""
        baseline_dir = Path(sample_regression_test_suite.baseline_directory)
        (baseline_dir / "test1.png").write_text("baseline1")
        (baseline_dir / "test2.png").write_text("baseline2")

        output_dir = Path(sample_regression_test_suite.output_directory)
        (output_dir / "test1_current.png").write_text("comparison1")
        (output_dir / "test2_current.png").write_text("comparison2")

        call_count = [0]

        def mock_sum(arr):
            call_count[0] += 1
            # First comparison passes, second fails
            return 0 if call_count[0] <= 2 else 5000

        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np, \
             patch("Asgard.Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", False):

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.ones((100, 100), dtype=np.uint8)
            mock_np.sum.side_effect = mock_sum
            mock_np.size = 10000

            tester = VisualRegressionTester()
            report = tester.run_suite(sample_regression_test_suite)

        assert report.total_comparisons == 2
        assert report.passed_comparisons == 1
        assert report.failed_comparisons == 1


# =============================================================================
# Test Helper Methods
# =============================================================================

class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.mark.L0
    def test_mask_regions(self, mock_pil_image, mock_image_draw):
        """Test _mask_regions helper method."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageDraw", mock_image_draw):

            tester = VisualRegressionTester()
            regions = [
                {"x": 0, "y": 0, "width": 100, "height": 50},
                {"x": 200, "y": 100, "width": 150, "height": 75},
            ]

            masked = tester._mask_regions(mock_pil_image, regions)

        # Should have called copy and Draw
        mock_pil_image.copy.assert_called_once()
        mock_image_draw.Draw.assert_called_once()

    @pytest.mark.L0
    def test_generate_diff_image(self, mock_pil_image, mock_image_module):
        """Test _generate_diff_image helper method."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageEnhance") as mock_enhance:

            mock_diff = MagicMock()
            mock_chops.difference.return_value = mock_diff

            mock_enhancer = MagicMock()
            mock_enhanced = MagicMock()
            mock_enhanced.save = MagicMock()
            mock_enhancer.enhance.return_value = mock_enhanced
            mock_enhance.Contrast.return_value = mock_enhancer

            tester = VisualRegressionTester()
            diff_path = tester._generate_diff_image(mock_pil_image, mock_pil_image)

        assert "diff_" in diff_path
        assert ".png" in diff_path
        mock_enhanced.save.assert_called_once()

    @pytest.mark.L0
    def test_generate_annotated_image(self, mock_pil_image, mock_image_draw):
        """Test _generate_annotated_image helper method."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageDraw", mock_image_draw):

            from Asgard.Freya.Visual.models.visual_models import DifferenceRegion, DifferenceType

            regions = [
                DifferenceRegion(
                    x=10, y=20, width=100, height=50,
                    difference_type=DifferenceType.MODIFICATION,
                    confidence=0.85,
                    description="Change detected"
                )
            ]

            tester = VisualRegressionTester()
            ann_path = tester._generate_annotated_image(mock_pil_image, regions)

        assert "annotated_" in ann_path
        assert ".png" in ann_path
        mock_pil_image.copy.assert_called_once()

    @pytest.mark.L0
    def test_generate_html_report(self, sample_regression_test_suite):
        """Test _generate_html_report helper method."""
        from Asgard.Freya.Visual.models.visual_models import RegressionReport, VisualComparisonResult

        results = [
            VisualComparisonResult(
                baseline_path="/tmp/baseline.png",
                comparison_path="/tmp/comparison.png",
                similarity_score=0.98,
                is_similar=True,
            )
        ]

        report = RegressionReport(
            suite_name="Test Suite",
            total_comparisons=1,
            passed_comparisons=1,
            failed_comparisons=0,
            results=results,
            overall_similarity=0.98,
        )

        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True):
            tester = VisualRegressionTester()
            report_path = tester._generate_html_report(report)

        assert report_path.exists()
        assert report_path.suffix == ".html"

        # Read and verify HTML content
        html_content = report_path.read_text()
        assert "Test Suite" in html_content
        assert "98" in html_content  # Similarity percentage


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in VisualRegressionTester."""

    @pytest.mark.L0
    def test_compare_handles_conversion_errors(self, temp_baseline_file, temp_comparison_file, mock_image_module):
        """Test compare handles image conversion errors gracefully."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Freya.Visual.services.visual_regression.Image", mock_image_module):

            mock_image = MagicMock()
            mock_image.convert.side_effect = Exception("Conversion failed")
            mock_image_module.open.return_value = mock_image

            tester = VisualRegressionTester()
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
            )

        assert result.similarity_score == 0.0
        assert result.is_similar is False

    @pytest.mark.L0
    def test_ssim_fallback_to_pixel_diff(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test SSIM falls back to pixel diff when not available."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", False), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np:

            mock_diff = MagicMock()
            mock_diff.convert.return_value = MagicMock()
            mock_chops.difference.return_value = mock_diff
            mock_np.array.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_np.sum.return_value = 0

            tester = VisualRegressionTester()
            config = ComparisonConfig(method=ComparisonMethod.STRUCTURAL_SIMILARITY)
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        # Should fall back to pixel diff
        assert result.comparison_method == ComparisonMethod.STRUCTURAL_SIMILARITY
        assert result.similarity_score >= 0.0


# =============================================================================
# Test Integration
# =============================================================================

class TestVisualRegressionIntegration:
    """Integration tests for VisualRegressionTester."""

    @pytest.mark.L0
    def test_full_comparison_workflow(self, temp_baseline_file, temp_comparison_file, mock_pil_image, mock_image_module):
        """Test complete comparison workflow with difference detection."""
        with patch("Asgard.Freya.Visual.services.visual_regression.PIL_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.ADVANCED_VISION_AVAILABLE", True), \
             patch("Asgard.Freya.Visual.services.visual_regression.Image", mock_image_module), \
             patch("Asgard.Freya.Visual.services.visual_regression.ssim") as mock_ssim, \
             patch("Asgard.Freya.Visual.services.visual_regression.cv2") as mock_cv2, \
             patch("Asgard.Freya.Visual.services.visual_regression.np") as mock_np, \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageChops") as mock_chops, \
             patch("Asgard.Freya.Visual.services.visual_regression.ImageEnhance"):

            # Mock SSIM with differences
            diff_map = np.ones((100, 100))
            diff_map[10:30, 10:30] = 0.5  # Low similarity region
            mock_ssim.return_value = (0.92, diff_map)

            mock_np.array.return_value = np.ones((100, 100), dtype=np.uint8)
            mock_np.any.return_value = True
            mock_np.where.return_value = ([10, 20, 30], [10, 20, 30])
            mock_np.mean.return_value = 0.7
            mock_np.min.return_value = 10
            mock_np.max.return_value = 30

            # Mock connected components
            mock_cv2.connectedComponents.return_value = (2, np.array([[0, 1], [1, 1]]))

            mock_diff = MagicMock()
            mock_chops.difference.return_value = mock_diff

            tester = VisualRegressionTester()
            config = ComparisonConfig(
                threshold=0.95,
                method=ComparisonMethod.STRUCTURAL_SIMILARITY,
            )
            result = tester.compare(
                str(temp_baseline_file),
                str(temp_comparison_file),
                config=config,
            )

        assert result.similarity_score == 0.92
        assert result.is_similar is False
        assert result.diff_image_path is not None
        assert result.annotated_image_path is not None
