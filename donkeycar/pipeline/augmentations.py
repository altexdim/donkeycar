import cv2
import numpy as np
import logging
import imgaug.augmenters as iaa
from donkeycar.config import Config


logger = logging.getLogger(__name__)


class Augmentations(object):
    """
    Some ready to use image augumentations.
    """

    @classmethod
    def crop(cls, left, right, top, bottom, keep_size=False):
        """
        The image augumentation sequence.
        Crops based on a region of interest among other things.
        left, right, top & bottom are the number of pixels to crop.
        """
        augmentation = iaa.Crop(px=(top, right, bottom, left),
                                keep_size=keep_size)
        return augmentation

    @classmethod
    def trapezoidal_mask(cls, lower_left, lower_right, upper_left, upper_right,
                         min_y, max_y):
        """
        Uses a binary mask to generate a trapezoidal region of interest.
        Especially useful in filtering out uninteresting features from an
        input image.
        """
        def _transform_images(images, random_state, parents, hooks):
            # Transform a batch of images
            transformed = []
            mask = None
            for image in images:
                if mask is None:
                    mask = np.zeros(image.shape, dtype=np.int32)
                    # # # # # # # # # # # # #
                    #       ul     ur          min_y
                    #
                    #
                    #
                    #    ll             lr     max_y
                    points = [
                        [upper_left, min_y],
                        [upper_right, min_y],
                        [lower_right, max_y],
                        [lower_left, max_y]
                    ]
                    cv2.fillConvexPoly(mask, np.array(points, dtype=np.int32),
                                       [255, 255, 255])
                    mask = np.asarray(mask, dtype='bool')

                masked = np.multiply(image, mask)
                transformed.append(masked)

            return transformed

        def _transform_keypoints(keypoints_on_images, random_state,
                                 parents, hooks):
            # No-op
            return keypoints_on_images

        augmentation = iaa.Lambda(func_images=_transform_images,
                                  func_keypoints=_transform_keypoints)
        return augmentation


class ImageAugmentation:
    def __init__(self, cfg, key):
        aug_list = getattr(cfg, key, [])
        augmentations = [ImageAugmentation.create(a, cfg) for a in aug_list]
        self.augmentations = iaa.Sequential(augmentations)

    @classmethod
    def create(cls, aug_type: str, config: Config) -> iaa.meta.Augmenter:
        """ Augmenatition factory. Cropping and trapezoidal mask are
            transfomations which should be applied in training, validation and
            inference. Multiply, Blur and similar are augmentations which should
            be used only in training. """

        if aug_type == 'CROP':
            logger.info(f'Creating augmentation {aug_type} with ROI_CROP ' 
                        f'L: {config.ROI_CROP_LEFT}, '
                        f'R: {config.ROI_CROP_RIGHT}, '
                        f'B: {config.ROI_CROP_BOTTOM}, ' 
                        f'T: {config.ROI_CROP_TOP}')

            return Augmentations.crop(left=config.ROI_CROP_LEFT,
                                      right=config.ROI_CROP_RIGHT,
                                      bottom=config.ROI_CROP_BOTTOM,
                                      top=config.ROI_CROP_TOP,
                                      keep_size=True)
        elif aug_type == 'TRAPEZE':
            logger.info(f'Creating augmentation {aug_type}')
            return Augmentations.trapezoidal_mask(
                        lower_left=config.ROI_TRAPEZE_LL,
                        lower_right=config.ROI_TRAPEZE_LR,
                        upper_left=config.ROI_TRAPEZE_UL,
                        upper_right=config.ROI_TRAPEZE_UR,
                        min_y=config.ROI_TRAPEZE_MIN_Y,
                        max_y=config.ROI_TRAPEZE_MAX_Y)

        elif aug_type == 'MULTIPLY':
            interval = getattr(config, 'AUG_MULTIPLY_RANGE', (0.5, 1.5))
            logger.info(f'Creating augmentation {aug_type} {interval}')
            return iaa.Multiply(interval)

        elif aug_type == 'BLUR':
            interval = getattr(config, 'AUG_BLUR_RANGE', (0.0, 3.0))
            logger.info(f'Creating augmentation {aug_type} {interval}')
            return iaa.GaussianBlur(sigma=interval)

        elif aug_type == 'CUSTOM':
            logger.info(f'Creating augmentation {aug_type}')

            # return iaa.Cartoon()

            seq = iaa.Sequential([
                iaa.Crop(percent=(0, 0.1)),  # random crops

                # Small gaussian blur with random sigma between 0 and 0.5.
                # But we only blur about 50% of all images.
                iaa.Sometimes(0.5, iaa.GaussianBlur(sigma=(0, 1.5))),

                # Strengthen or weaken the contrast in each image.
                iaa.LinearContrast((0.75, 1.5)),

                # Add gaussian noise.
                # For 50% of all images, we sample the noise once per pixel.
                # For the other 50% of all images, we sample the noise per pixel AND
                # channel. This can change the color (not only brightness) of the
                # pixels.
                iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.05 * 255), per_channel=0.5),

                # Make some images brighter and some darker.
                # In 20% of all cases, we sample the multiplier once per channel,
                # which can end up changing the color of the images.
                # iaa.Multiply((0.8, 1.2), per_channel=0.2),

                # Apply affine transformations to each image.
                # Scale/zoom them, translate/move them, rotate them and shear them.
                iaa.Affine(
                    # scale={"x": (0.1, 1.1), "y": (0.1, 1.1)},
                    translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
                    rotate=(-5, 5),
                    # shear=(-8, 8)
                ),

                # -------------------------------------------------
                iaa.SomeOf(3, [
                    # Add values to the pixels of images with possibly different values for neighbouring pixels.
                    # iaa.AddElementwise((-40, 40), per_channel=0.5),
                    iaa.AddElementwise((-40, 40), per_channel=False),
                    # aug = iaa.AdditiveGaussianNoise(scale=0.2*255, per_channel=True)

                    # aug = iaa.MultiplyElementwise((0.5, 1.5), per_channel=0.5)
                    # iaa.Multiply((0.5, 1.5), per_channel=0.5),
                    iaa.Multiply((0.5, 1.5), per_channel=False),

                    # aug = iaa.Cutout(nb_iterations=(1, 5), size=0.1, squared=False)
                    # aug = iaa.CoarseDropout(0.02, size_percent=0.15, per_channel=0.5)
                    iaa.CoarseDropout((0.0, 0.05), size_percent=(0.02, 0.25)),

                    # iaa.Invert(0.25, per_channel=0.5),

                    # aug = iaa.JpegCompression(compression=(70, 99))

                    # iaa.AddToHueAndSaturation((-50, 50), per_channel=True),
                    iaa.AddToHueAndSaturation((-50, 50), per_channel=False),
                    iaa.ChangeColorTemperature((1100, 10000)),

                    # aug = iaa.GammaContrast((0.5, 2.0))
                    # iaa.GammaContrast((0.5, 2.0), per_channel=True),
                    iaa.GammaContrast((0.5, 2.0), per_channel=False),

                    # iaa.Sharpen(alpha=(0.0, 1.0), lightness=(0.75, 2.0)),
                    iaa.imgcorruptlike.GaussianNoise(severity=2),
                    iaa.imgcorruptlike.Fog(severity=1)
                ])
            ], random_order=True)  # apply augmenters in random order

            return seq

    # Parts interface
    def run(self, img_arr):
        aug_img_arr = self.augmentations.augment_image(img_arr)
        return aug_img_arr
