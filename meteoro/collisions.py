"""Choques de la partida: balas contra meteoros y naves, y todo contra el jugador."""
import pygame

from . import config as C
from . import rules

circle = pygame.sprite.collide_circle


def resolve(play):
    _player_bullets(play)
    _player(play)


def _player_bullets(play):
    hits = pygame.sprite.groupcollide(play.meteors, play.bullets, False, True, circle)
    for meteor, bullets in hits.items():
        for bullet in bullets:
            bullet.volley.bullet_hit()
        if meteor.alive():
            play.destroy_meteor(meteor)

    for group in (play.enemies, play.bosses):
        hits = pygame.sprite.groupcollide(group, play.bullets, False, True, circle)
        for ship, bullets in hits.items():
            for bullet in bullets:
                bullet.volley.bullet_hit()
            if not ship.alive():
                continue
            if ship.damage(len(bullets), play.world_now):
                play.destroy_ship(ship)
            else:
                play.audio.play("hit")
                play.particles.emit(bullets[0].rect.midtop, 6, [(255, 255, 200), (255, 180, 80)],
                                    speed=(60, 180), life=(0.15, 0.35))


def _player(play):
    player = play.player
    if not player.alive_ship:
        return

    # Power-ups: se recogen aunque la nave esté parpadeando
    for powerup in pygame.sprite.spritecollide(player, play.powerups, True, circle):
        play.apply_powerup(powerup.kind)

    if player.is_invulnerable(play.now):
        return

    hits = pygame.sprite.spritecollide(player, play.meteors, True, circle)
    if hits:
        damage = sum(rules.meteor_damage(m.size) for m in hits)
        for meteor in hits:
            play.explode(meteor.rect.center, C.METEOR_EXPLOSION[meteor.size], sound=False)
        play.damage_player(damage, hits[0].rect.center)
        return

    hits = pygame.sprite.spritecollide(player, play.enemy_bullets, True, circle)
    if hits:
        play.damage_player(C.ENEMY_BULLET_DAMAGE * len(hits), hits[0].rect.center)
        return

    hits = pygame.sprite.spritecollide(player, play.enemies, False, circle)
    if hits:
        play.destroy_ship(hits[0])
        play.damage_player(C.ENEMY_DAMAGE, hits[0].rect.center)
        return

    boss = play.boss
    if boss and circle(player, boss):
        play.damage_player(C.BOSS_DAMAGE, player.rect.midtop)
