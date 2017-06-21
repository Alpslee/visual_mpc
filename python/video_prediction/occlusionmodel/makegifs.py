import cPickle
import numpy
from video_prediction.utils_vpred.create_gif import *
from PIL import Image

def add_crosshairs(distrib, pix_list):
    """
    add crosshairs to video
    :param distrib:
    :param pix_list: list of x, y coords
    :return:
    """
    batch = pix_list[0].shape[0]
    for b in range(batch):
        for i in range(len(pix_list)):
            x, y = pix_list[i][b]
            distrib[i][b, x] = 0
            distrib[i][b, :, y] = 0

    return distrib


def comp_gif(conf, file_path, name= None, examples = 10, show_parts=False):
    dict_ = cPickle.load(open(file_path + '/dict_.pkl', "rb"))

    ground_truth =dict_['ground_truth']
    gen_images = dict_['gen_images']
    object_masks = dict_['object_masks']

    moved_images = dict_['moved_images']
    moved_images = prepare_masks(moved_images, copy_last_dim=False)

    trafos = dict_['trafos']
    comp_factors = dict_['comp_factors']
    comp_factors = [np.stack(c) for c in comp_factors]

    print 'finished loading ...'

    img = create_images(object_masks, examples)
    img = Image.fromarray(img)
    img.save(file_path +'/objectparts_masks.png')

    if not isinstance(ground_truth, list):
        ground_truth = np.split(ground_truth, ground_truth.shape[1], axis=1)
        ground_truth = [np.squeeze(g) for g in ground_truth]

    videolist = [ground_truth, gen_images] + moved_images

    if show_parts:
        moved_parts = dict_['moved_parts']
        moved_parts = prepare_masks(moved_parts, copy_last_dim=False)
        videolist += moved_parts

    suffix = ''
    itr_vis = re.match('.*?([0-9]+)$', conf['visualize']).group(1)

    fused_gif = assemble_gif(videolist, num_exp= examples)
    npy_to_gif(fused_gif, file_path + '/vid_'+itr_vis+ suffix)

def create_images(object_masks, nexp):
    object_masks = [np.repeat(m, 3, axis=-1) for m in object_masks]
    rows = []

    num_objects = len(object_masks)
    for ob in range(num_objects):
        maskrow = []
        for ex in range(nexp):
            maskrow.append(object_masks[ob][ex])
        rows.append(np.concatenate(maskrow, axis=1))

    combined = (np.concatenate(rows, axis=0)*255.).astype(np.uint8)
    return combined

def prepare_masks(masks, copy_last_dim):
    tsteps = len(masks)
    nmasks = len(masks[0])
    list_of_maskvideos = []

    for m in range(nmasks):  # for timesteps
        mask_video = []
        for t in range(tsteps):
            if copy_last_dim:
                single_mask_batch = np.repeat(masks[t][m], 3, axis=3 )
            else:
                single_mask_batch = masks[t][m]
            mask_video.append(single_mask_batch)
        list_of_maskvideos.append(mask_video)

    return list_of_maskvideos


def pad_pos(conf, vid, pos, origsize = 64):

    batch = vid[0].shape[0]
    padded_vid = [np.zeros([batch, origsize, origsize, 3]) for _ in range(len(vid))]

    retina_size = conf['retina_size']
    halfret = retina_size /2

    for b in range(batch):
        for t in range(len(vid)):
            rstart = pos[t][b,0] - halfret
            rend = pos[t][b,0] + halfret + 1
            cstart = pos[t][b,1] - halfret
            cend = pos[t][b,1] + halfret + 1
            padded_vid[t][b, rstart:rend, cstart:cend] = vid[t][b]

    return padded_vid

if __name__ == '__main__':
    file_path = '/home/frederik/Documents/lsdc/tensorflow_data/occulsionmodel/firsttest'
    hyperparams = imp.load_source('hyperparams', file_path +'/conf.py')

    conf = hyperparams.configuration
    conf['visualize'] = conf['output_dir'] + '/model24002'


    comp_gif(conf, file_path + '/modeldata')