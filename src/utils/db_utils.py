def db_check_if_exists(sess, cls, obj_id) -> bool:
    q_exists = sess.query(cls).filter(cls.id == obj_id).exists()
    return sess.query(q_exists).scalar()
