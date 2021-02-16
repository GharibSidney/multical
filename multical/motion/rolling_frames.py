from multical.motion.static_frames import project_cameras
from cached_property import cached_property
import numpy as np
from structs.struct import struct, subset
from .motion_model import MotionModel

from multical.optimization.parameters import IndexMapper, Parameters
from multical import tables
from structs.numpy import Table

from multical.transform import rtvec
from multical.transform.interpolate import lerp


def rolling_times(cameras, point_table):
  image_heights = np.array([camera.image_size[1] for camera in cameras])    
  return point_table.points[..., 1] / np.expand_dims(image_heights, (1,2,3))  


def transformed_linear(self, camera_poses, board_poses, board_points, times):
  
  pose_start = struct(camera=camera_poses, board=board_poses, times=self.pose_start)
  pose_end = pose_start._extend(times=self.pose_end)

  table_start = tables.expand_poses(pose_start)
  table_end = tables.expand_poses(pose_end)

  start_frame = tables.transform_points(table_start, board_points)
  end_frame = tables.transform_points(table_end, board_points)

  return struct(
    points = lerp(start_frame.points, end_frame.points, times),
    valid = start_frame.valid & end_frame.valid
  )



class RollingFrames(MotionModel, Parameters):

  def __init__(self, pose_start, pose_end, valid, names):
    self.pose_start = pose_start
    self.pose_end = pose_end
    self.valid = valid
    self.names = names

  @property
  def size(self):
    return self.poses.shape[0]

  @cached_property
  def valid(self):
    return self.pose_table.valid

  @cached_property
  def start_table(self):
     return Table.build(poses=self.pose_start, valid=self.valid)
  
  @cached_property
  def end_table(self):
    return Table.build(poses=self.pose_end, valid=self.valid)
  

  @staticmethod
  def init(pose_table, names=None):
    size = pose_table.valid.size
    names = names or [str(i) for i in range(size)]


  def _project(self, cameras, camera_poses, board_poses, board_points, estimates):
    times = rolling_times(cameras, estimates) if estimates is not None\
      else np.full(board_points.points.shape, 0.5)
    
    transformed = transformed_linear(self, camera_poses, 
      board_poses, board_points, times)

    return project_cameras(cameras, transformed)

  def project(self, cameras, camera_poses, board_poses, board_points, estimates=None):
    if estimates is not None:
      return self._project(cameras, camera_poses, board_poses, estimates)


  @cached_property
  def params(self):
    return [
      rtvec.from_matrix(self.pose_start).ravel(),
      rtvec.from_matrix(self.pose_end).ravel()
    ]
      
  def with_params(self, params):
    start, end = [rtvec.to_matrix(m.reshape(-1, 6)) for m in params]
    return self.copy(pose_start=start, pose_end=end)

  def sparsity(self, index_mapper : IndexMapper, axis : int):
    return [index_mapper.pose_mapping(t, axis=axis, param_size=6) 
      for t in [self.start_table, self.end_table]]

  def export(self):
    return {i:struct(start=start.poses.tolist(), end=end.poses.tolist()) 
      for i, start, end, valid in zip(self.names, self.pose_start, self.pose_end, self.valid) 
        if valid}

  def __getstate__(self):
    attrs = ['pose_start', 'pose_end', 'valid']
    return subset(self.__dict__, attrs)

  def copy(self, **k):
    """Copy object and change some attribute (no mutation)"""
    d = self.__getstate__()
    d.update(k)
    return self.__class__(**d)
  



  # @cached_property
  # def transformed_rolling(self):
  #   poses = self.pose_estimates
  #   start_frame = np.expand_dims(poses.rig.poses, (0, 2, 3))
  #   end_frame = np.expand_dims(self.frame_motion.poses, (0, 2, 3))
    
  #   frame_poses = interpolate_poses(start_frame, end_frame, self.times)
  #   view_poses = np.expand_dims(poses.camera.poses, (1, 2, 3)) @ frame_poses  

  #   board_points = self.stacked_boards
  #   board_points_t = matrix.transform_homog(t = np.expand_dims(poses.board.poses, 1), points = board_points.points)

  #   return struct(
  #     points = matrix.transform_homog(t = view_poses, points = np.expand_dims(board_points_t, (0, 1))),
  #     valid = self.valid
  #   )

 