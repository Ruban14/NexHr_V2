import {
  animate,
  group,
  query,
  style,
  transition,
  trigger,
} from '@angular/animations';

export const routeAnimations = trigger('routeAnimations', [
  transition('* <=> *', [
    query(
      ':enter, :leave',
      [
        style({
          position: 'absolute',
          inset: 0,
          width: '100%',
        }),
      ],
      { optional: true },
    ),
    group([
      query(
        ':leave',
        [animate('180ms ease-in', style({ opacity: 0, transform: 'translateY(8px)' }))],
        { optional: true },
      ),
      query(
        ':enter',
        [
          style({ opacity: 0, transform: 'translateY(12px)' }),
          animate('260ms 80ms ease-out', style({ opacity: 1, transform: 'translateY(0)' })),
        ],
        { optional: true },
      ),
    ]),
  ]),
]);
